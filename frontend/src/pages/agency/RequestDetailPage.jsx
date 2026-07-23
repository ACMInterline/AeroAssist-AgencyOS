import { useEffect, useState } from "react"
import DetailSummary from "../../components/DetailSummary"
import EmptyState from "../../components/EmptyState"
import PageHeader from "../../components/PageHeader"
import ProtectedRoute from "../../components/ProtectedRoute"
import RequestStatusBadge from "../../components/RequestStatusBadge"
import SecondaryButton from "../../components/SecondaryButton"
import Timeline from "../../components/Timeline"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function RequestDetailPage({ requestId }) {
  const [state, setState] = useState(null)
  const [identityDrafts, setIdentityDrafts] = useState({})
  const [confirmingIdentity, setConfirmingIdentity] = useState("")
  const [identityError, setIdentityError] = useState({ id: "", message: "" })
  const [forms, setForms] = useState({
    status: "triage",
    passenger_id: "",
    relationship_id: "",
    sequence: 1,
    origin_text: "",
    destination_text: "",
    service_code: "",
    service_name: "",
    service_category: "general",
    message_text: "",
    task_title: "",
  })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/requests/${requestId}`)
    const passengers = await apiGet(`/api/agencies/${context.agency.id}/passengers`)
    const relationships = await apiGet(`/api/agencies/${context.agency.id}/client-passenger-relationships`)
    setState({ ...context, ...detail, agencyPassengers: passengers.items, agencyRelationships: relationships.items })
    setIdentityDrafts((current) => Object.fromEntries(
      (detail.passengers || []).filter((passenger) => !passenger.passenger_id).map((passenger) => {
        const proposed = passenger.proposed_identity_json || {}
        return [passenger.id, current[passenger.id] || {
          existing_passenger_id: "",
          first_name: proposed.first_name || "",
          middle_name: proposed.middle_name || "",
          last_name: proposed.last_name || "",
          display_name: proposed.display_name || "",
          date_of_birth: proposed.date_of_birth || "",
          passenger_type: proposed.passenger_type || passenger.snapshot_passenger_type || "ADT",
          relationship_type: "other",
          confirmation_reason: "",
        }]
      }),
    ))
    setForms((current) => ({
      ...current,
      status: detail.request.status,
      passenger_id: passengers.items[0]?.id || "",
      relationship_id: "",
      sequence: (detail.segments?.length || 0) + 1,
    }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [requestId])

  function setField(name, value) {
    setForms((current) => ({ ...current, [name]: value }))
  }

  function setIdentityField(requestPassengerId, name, value) {
    setIdentityDrafts((current) => ({
      ...current,
      [requestPassengerId]: { ...(current[requestPassengerId] || {}), [name]: value },
    }))
  }

  async function changeStatus(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/requests/${requestId}/status`, { status: forms.status, summary: `Status changed to ${forms.status}` })
    await load()
  }

  async function addPassenger(event) {
    event.preventDefault()
    const payload = { passenger_id: forms.passenger_id, role_in_request: "traveler", is_primary_traveler: state.passengers.length === 0 }
    if (forms.relationship_id) payload.client_passenger_relationship_id = forms.relationship_id
    await apiPost(`/api/agencies/${state.agency.id}/requests/${requestId}/passengers`, payload)
    await load()
  }

  async function confirmIdentity(event, requestPassenger) {
    event.preventDefault()
    const draft = identityDrafts[requestPassenger.id] || {}
    const payload = draft.existing_passenger_id
      ? {
          existing_passenger_id: draft.existing_passenger_id,
          relationship_type: draft.relationship_type || "other",
          confirmation_reason: draft.confirmation_reason,
        }
      : {
          first_name: draft.first_name,
          middle_name: draft.middle_name || undefined,
          last_name: draft.last_name,
          display_name: draft.display_name || undefined,
          date_of_birth: draft.date_of_birth,
          passenger_type: draft.passenger_type || "ADT",
          relationship_type: draft.relationship_type || "other",
          confirmation_reason: draft.confirmation_reason,
        }
    setIdentityError({ id: "", message: "" })
    setConfirmingIdentity(requestPassenger.id)
    try {
      await apiPost(`/api/agencies/${state.agency.id}/requests/${requestId}/passengers/${requestPassenger.id}/confirm-identity`, payload)
      await load()
    } catch (err) {
      setIdentityError({ id: requestPassenger.id, message: err.message })
    } finally {
      setConfirmingIdentity("")
    }
  }

  async function addSegment(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/requests/${requestId}/segments`, {
      sequence: Number(forms.sequence),
      origin_text: forms.origin_text,
      destination_text: forms.destination_text,
    })
    setField("origin_text", "")
    setField("destination_text", "")
    await load()
  }

  async function addService(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/requests/${requestId}/services`, {
      service_code: forms.service_code,
      service_name: forms.service_name,
      service_category: forms.service_category,
      status: "requested",
    })
    setForms((current) => ({ ...current, service_code: "", service_name: "" }))
    await load()
  }

  async function addMessage(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/requests/${requestId}/messages`, {
      sender_type: "staff",
      visibility: "client_visible",
      message_text: forms.message_text,
    })
    setField("message_text", "")
    await load()
  }

  async function addTask(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/requests/${requestId}/tasks`, {
      title: forms.task_title,
      priority: "normal",
      visibility: "internal",
    })
    setField("task_title", "")
    await load()
  }

  async function archiveOrRestore() {
    const action = state.request.status === "archived" ? "restore" : "archive"
    await apiPost(`/api/agencies/${state.agency.id}/requests/${requestId}/${action}`)
    await load()
  }

  async function createTripDossier() {
    window.location.href = `/agency/request-trip-conversion?request_id=${encodeURIComponent(requestId)}`
  }

  async function unlinkTripDossier() {
    if (!state.linked_trip) return
    await apiPost(`/api/agencies/${state.agency.id}/trips/${state.linked_trip.id}/unlink-request/${requestId}`)
    await load()
  }

  const allowedRelationships = (state?.agencyRelationships || []).filter((relationship) => relationship.client_id === state?.request?.client_id && relationship.passenger_id === forms.passenger_id && relationship.status === "active")
  const requestReady = Boolean(state?.passengers?.length && state?.segments?.length)
  const unresolvedPassengerCount = (state?.passengers || []).filter((passenger) => !passenger.passenger_id || ["unresolved", "source_quarantined"].includes(passenger.identity_status)).length
  const identitiesConfirmed = requestReady && unresolvedPassengerCount === 0
  const requestClosed = ["cancelled", "archived"].includes(state?.request?.status)
  const isCanonicalV4 = state?.request?.request_version === 4

  if (!state) {
    return (
      <AgencyLayout>
        <ProtectedRoute loading={!error} error={error} />
      </AgencyLayout>
    )
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Requests", href: "/agency/requests" }, { label: state?.request?.request_reference || "Request" }]}
            eyebrow={state?.request?.request_reference}
            title={state?.request?.title}
            description="The client’s requested journey and services. Flight details remain planned until a booking is confirmed."
            status={<RequestStatusBadge status={state?.request?.status} />}
            actions={<div className="flex flex-wrap gap-2">
              {isCanonicalV4 ? <a className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" href={`/agency/requests/new?edit_request_id=${encodeURIComponent(requestId)}`}>Edit request</a> : null}
              <SecondaryButton onClick={archiveOrRestore}>{state?.request?.status === "archived" ? "Restore request" : "Archive request"}</SecondaryButton>
            </div>}
          />
          {isCanonicalV4 ? <p className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">Journey, traveler, assistance, animal, and special-item changes are kept together. Use Edit request to update this request safely.</p> : <p className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">This earlier request remains readable. Reconcile it before using the unified request editor.</p>}
          <WorkflowContinuityPanel
            breadcrumbs={[{ label: "Clients", href: state?.client?.id ? `/agency/clients/${state.client.id}` : "/agency/clients" }, { label: "Requests", href: "/agency/requests" }]}
            currentLabel={state?.request?.request_reference || "Request"}
            status={state?.request?.status}
            validation={identitiesConfirmed && !requestClosed
              ? { state: "ready", label: "Ready to prepare the trip", reason: "Passenger identities and flight details are available for review." }
              : requestReady && !requestClosed
                ? { state: "warning", label: "Passenger identity confirmation needed", reason: "The trip may be prepared for planning, but an offer cannot be created until every traveler is confirmed." }
              : { state: requestClosed ? "blocked" : "warning", label: requestClosed ? "Request closed" : "More trip details needed", reason: requestClosed ? "Restore the request before continuing." : "Add at least one passenger and one flight segment before preparing the trip." }}
            previous={state?.passengers?.[0]?.passenger_id ? { label: "Previous: passenger", href: `/agency/passengers/${state.passengers[0].passenger_id}` } : { label: "Previous: client", href: state?.client?.id ? `/agency/clients/${state.client.id}` : "/agency/clients" }}
            next={state?.linked_trip
              ? { label: "Continue to trip", href: `/agency/trips/${state.linked_trip.id}` }
              : { label: "Prepare trip", href: `/agency/request-trip-conversion?request_id=${encodeURIComponent(requestId)}`, enabled: requestReady && !requestClosed, reason: "Passenger and flight details are required." }}
            relatedRecords={[
              { label: "Client", value: state?.client?.display_name, href: state?.client?.id ? `/agency/clients/${state.client.id}` : undefined },
              { label: "Passengers", value: unresolvedPassengerCount ? `${state?.passengers?.length || 0} (${unresolvedPassengerCount} unresolved)` : state?.passengers?.length || 0 },
              { label: "Trip", value: state?.linked_trip?.trip_reference || "not converted", href: state?.linked_trip ? `/agency/trips/${state.linked_trip.id}` : undefined },
            ]}
          />
          <DetailSummary title="Request summary" columns={4} items={[
            { label: "Client", value: state?.client?.display_name },
            { label: "Priority", value: state?.request?.priority },
            { label: "Received through", value: state?.request?.source?.replaceAll("_", " ") },
            { label: "Route", value: state?.request?.route_summary || "Not set" },
            { label: "Passengers", value: state?.request?.passenger_count ?? 0 },
            { label: "Pets", value: state?.request?.pet_count ?? 0 },
            { label: "Special services", value: state?.request?.special_service_count ?? 0 },
            { label: "Journey type", value: state?.request?.trip_type?.replaceAll("_", " ") || "Unknown" },
          ]} />
          <section className="grid gap-4 lg:grid-cols-3">
            <InfoCard title="Operational flags" rows={[
              ["Medical review", state?.request?.requires_medical_review ? "Required" : "No"],
              ["Policy review", state?.request?.requires_airline_policy_review ? "Required" : "No"],
              ["Document follow-up", state?.request?.requires_document_followup ? "Required" : "No"],
              ["Existing passenger links", state?.request?.has_existing_passenger_links ? "Yes" : "No"],
            ]} />
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Status</h3>
              <form className="mt-4 flex gap-2" onSubmit={changeStatus}>
                <select className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.status} onChange={(event) => setField("status", event.target.value)}>
                  {["draft", "new", "triage", "waiting_for_client", "in_progress", "ready_for_offer", "offer_created", "closed", "cancelled", "archived"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                </select>
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Update</button>
              </form>
              <p className="mt-3 text-sm text-slate-600">Offer workspace status is managed in the offer builder.</p>
            </div>
            <InfoCard title="Notes" rows={[
              ["Client notes", state?.request?.client_notes || "None"],
              ["Internal notes", state?.request?.internal_notes || "None"],
              ["Client-visible", state?.request?.client_visible_notes || "None"],
            ]} />
          </section>
          <Panel title="Trip">
            {state?.linked_trip ? (
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-950">{state.linked_trip.trip_reference} · {state.linked_trip.trip_title}</p>
                  <p className="mt-1 text-sm text-slate-600">{state.linked_trip.trip_status.replaceAll("_", " ")} · {state.linked_trip.route_summary || "Route pending"}</p>
                  <p className="mt-1 text-xs text-slate-500">This request remains the original client brief while the linked trip holds day-to-day travel work.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <a className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" href={`/agency/trips/${state.linked_trip.id}`}>Open trip</a>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={unlinkTripDossier}>Unlink</button>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-950">No trip prepared yet</p>
                  <p className="mt-1 text-sm text-slate-600">Prepare a trip when this request is ready for active travel work. The original request stays unchanged.</p>
                </div>
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={createTripDossier}>Prepare trip</button>
              </div>
            )}
          </Panel>
          <AirlineIntelLinkPanel
            title="Search Airline Intelligence"
            airlineCode={state.segments.find((segment) => segment.preferred_airline_code)?.preferred_airline_code}
            serviceCodes={state.services.map((service) => service.service_code)}
          />
          <Panel title="Special Services">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-950">Passenger service checks</p>
                <p className="mt-1 text-sm text-slate-600">Rules evaluation and SSR/OSI previews for this request.</p>
              </div>
              <a className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" href={`/agency/requests/${requestId}/special-services`}>Open Special Services</a>
            </div>
          </Panel>
          <Panel title="Attention needed">
            <List items={state.case_flags} empty="Nothing needs attention" render={(item) => `${item.flag_label} · ${item.severity} · ${item.source}`} />
          </Panel>
          <Panel title="Passengers">
            {!isCanonicalV4 ? <form className="grid gap-3 md:grid-cols-[1fr_1fr_auto]" onSubmit={addPassenger}>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.passenger_id} onChange={(event) => setField("passenger_id", event.target.value)}>
                {state.agencyPassengers.map((passenger) => <option key={passenger.id} value={passenger.id}>{passenger.display_name}</option>)}
              </select>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.relationship_id} onChange={(event) => setField("relationship_id", event.target.value)}>
                <option value="">No relationship selected</option>
                {allowedRelationships.map((relationship) => <option key={relationship.id} value={relationship.id}>{relationship.relationship_type.replaceAll("_", " ")}</option>)}
              </select>
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add passenger</button>
            </form> : null}
            {!state.passengers.length ? <p className="text-sm text-slate-500">No passengers linked yet</p> : null}
            <div className="space-y-3">
              {state.passengers.map((item) => {
                const unresolved = !item.passenger_id || ["unresolved", "source_quarantined"].includes(item.identity_status)
                const draft = identityDrafts[item.id] || {}
                return (
                  <div className="rounded-md border border-slate-200 p-4" key={item.id}>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-slate-950">{item.snapshot_display_name}</p>
                        <p className="mt-1 text-xs text-slate-600">{item.snapshot_passenger_type} · {item.role_in_request.replaceAll("_", " ")} · {unresolved ? "identity unresolved" : "identity confirmed"}</p>
                      </div>
                      {!unresolved ? <a className="text-sm font-semibold text-blue-700" href={`/agency/passengers/${item.passenger_id}`}>Open passenger</a> : null}
                    </div>
                    {unresolved ? (
                      <form className="mt-4 space-y-3 border-t border-slate-100 pt-4" onSubmit={(event) => confirmIdentity(event, item)}>
                        {identityError.id === item.id ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800">{identityError.message}</p> : null}
                        {item.identity_status === "source_quarantined" ? <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">A legacy synthetic profile was quarantined. Confirm the real traveler before continuing to an offer.</p> : null}
                        <p className="text-sm text-slate-700">Choose an existing passenger or enter confirmed identity details. A new master profile is created only by this action.</p>
                        <div className="grid gap-3 md:grid-cols-3">
                          <label className="text-sm font-medium text-slate-700">Existing passenger
                            <select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.existing_passenger_id || ""} onChange={(event) => setIdentityField(item.id, "existing_passenger_id", event.target.value)}>
                              <option value="">Create from confirmed details</option>
                              {state.agencyPassengers.map((passenger) => <option key={passenger.id} value={passenger.id}>{passenger.display_name}</option>)}
                            </select>
                          </label>
                          <label className="text-sm font-medium text-slate-700">Relationship
                            <select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.relationship_type || "other"} onChange={(event) => setIdentityField(item.id, "relationship_type", event.target.value)}>
                              {["self", "spouse", "child", "parent", "guardian", "employee", "assistant", "company_traveler", "other"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                            </select>
                          </label>
                          <label className="text-sm font-medium text-slate-700">Confirmation reason
                            <input required minLength={3} className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.confirmation_reason || ""} onChange={(event) => setIdentityField(item.id, "confirmation_reason", event.target.value)} />
                          </label>
                        </div>
                        {!draft.existing_passenger_id ? (
                          <div className="grid gap-3 md:grid-cols-3">
                            <label className="text-sm font-medium text-slate-700">First name<input required className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.first_name || ""} onChange={(event) => setIdentityField(item.id, "first_name", event.target.value)} /></label>
                            <label className="text-sm font-medium text-slate-700">Middle name<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.middle_name || ""} onChange={(event) => setIdentityField(item.id, "middle_name", event.target.value)} /></label>
                            <label className="text-sm font-medium text-slate-700">Last name<input required className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.last_name || ""} onChange={(event) => setIdentityField(item.id, "last_name", event.target.value)} /></label>
                            <label className="text-sm font-medium text-slate-700">Display name<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.display_name || ""} onChange={(event) => setIdentityField(item.id, "display_name", event.target.value)} /></label>
                            <label className="text-sm font-medium text-slate-700">Date of birth<input required type="date" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.date_of_birth || ""} onChange={(event) => setIdentityField(item.id, "date_of_birth", event.target.value)} /></label>
                            <label className="text-sm font-medium text-slate-700">Passenger type
                              <select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.passenger_type || "ADT"} onChange={(event) => setIdentityField(item.id, "passenger_type", event.target.value)}>
                                {["ADT", "CHD", "INF", "YTH", "SRC", "STU", "UMNR", "INS", "other"].map((value) => <option key={value} value={value}>{value}</option>)}
                              </select>
                            </label>
                          </div>
                        ) : null}
                        <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60" disabled={confirmingIdentity === item.id} type="submit">{confirmingIdentity === item.id ? "Confirming..." : "Confirm identity"}</button>
                      </form>
                    ) : null}
                  </div>
                )
              })}
            </div>
          </Panel>
          <Panel title="Intended itinerary">
            {!isCanonicalV4 ? <form className="grid gap-3 md:grid-cols-[80px_1fr_1fr_auto]" onSubmit={addSegment}>
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" type="number" value={forms.sequence} onChange={(event) => setField("sequence", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Origin" value={forms.origin_text} onChange={(event) => setField("origin_text", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Destination" value={forms.destination_text} onChange={(event) => setField("destination_text", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add segment</button>
            </form> : null}
            <List items={state.segments} empty="No intended segments yet" render={(item) => `${item.sequence}. ${item.origin_text} to ${item.destination_text}${item.departure_date ? ` · ${item.departure_date}` : ""}${item.preferred_flight_number ? ` · ${item.preferred_flight_number}` : ""}${item.cabin_preference ? ` · ${item.cabin_preference}` : ""}`} />
          </Panel>
          <Panel title="Requested services">
            {!isCanonicalV4 ? <form className="grid gap-3 md:grid-cols-[120px_1fr_1fr_auto]" onSubmit={addService}>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Code" value={forms.service_code} onChange={(event) => setField("service_code", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Service name" value={forms.service_name} onChange={(event) => setField("service_name", event.target.value)} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Category" value={forms.service_category} onChange={(event) => setField("service_category", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add service</button>
            </form> : null}
            <List items={state.services} empty="No services requested yet" render={(item) => `${item.service_code} · ${item.service_name} · ${item.status.replaceAll("_", " ")}${item.detail_payload && Object.keys(item.detail_payload).length ? ` · ${detailSummary(item.service_category, item.detail_payload)}` : ""}`} />
          </Panel>
          <Panel title="Services by passenger and flight">
            <List items={state.passenger_segment_services} empty="No passenger and flight service details yet" render={(item) => {
              const passenger = state.passengers.find((entry) => entry.id === item.request_passenger_id)
              const segment = state.segments.find((entry) => entry.id === item.request_segment_id)
              return `${passenger?.snapshot_display_name || "Passenger"} · ${segment ? `${segment.origin_text} → ${segment.destination_text}` : "Segment"} · ${item.service_code} · ${item.applicability_status.replaceAll("_", " ")}${item.service_family_code ? ` · ${item.service_family_code.replaceAll("_", " ")}` : ""}`
            }} />
          </Panel>
          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Pets and segment transport">
              <List items={state.pets} empty="No pets captured yet" render={(item) => `${item.pet_name || "Pet"} · ${item.species}${item.breed || item.breed_free_text ? ` · ${item.breed || item.breed_free_text}` : ""} · ${item.requested_transport_mode || "mode pending"}`} />
              <List items={state.pet_segment_transport} empty="No pet segment transport rows yet" render={(item) => {
                const pet = state.pets.find((entry) => entry.id === item.request_pet_id)
                const segment = state.segments.find((entry) => entry.id === item.request_segment_id)
                return `${pet?.pet_name || "Pet"} · ${segment ? `${segment.origin_text} → ${segment.destination_text}` : "Segment"} · ${item.requested_transport_mode || item.transport_mode || "pending"}`
              }} />
            </Panel>
            <Panel title="Special items and segment transport">
              <List items={state.special_items} empty="No special items captured yet" render={(item) => `${item.item_name || item.item_category_code || item.item_type} · ${item.description} · ${item.transport_location || "location pending"}`} />
              <List items={state.special_item_segments} empty="No item segment transport rows yet" render={(item) => {
                const specialItem = state.special_items.find((entry) => entry.id === item.request_special_item_id)
                const segment = state.segments.find((entry) => entry.id === item.request_segment_id)
                return `${specialItem?.item_name || specialItem?.item_category_code || "Item"} · ${segment ? `${segment.origin_text} → ${segment.destination_text}` : "Segment"} · ${item.transport_location || "pending"}`
              }} />
            </Panel>
          </section>
          <Panel title="Advanced source details">
            <InfoCard title="Record details" rows={[
              ["Request format", isCanonicalV4 ? "Unified request" : "Earlier request"],
              ["Source", state.request?.source?.replaceAll("_", " ") || "Unknown"],
              ["Passenger identity", unresolvedPassengerCount ? `${unresolvedPassengerCount} awaiting confirmation` : "Confirmed"],
              ["Compatibility", isCanonicalV4 ? "Operational views synchronized" : "Manual reconciliation required"],
            ]} />
          </Panel>
          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Messages">
              <form className="flex gap-2" onSubmit={addMessage}>
                <input required className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Message text" value={forms.message_text} onChange={(event) => setField("message_text", event.target.value)} />
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add</button>
              </form>
              <List items={state.messages} empty="No messages yet" render={(item) => `${item.visibility.replaceAll("_", " ")} · ${item.message_text}`} />
            </Panel>
            <Panel title="Tasks">
              <form className="flex gap-2" onSubmit={addTask}>
                <input required className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Task title" value={forms.task_title} onChange={(event) => setField("task_title", event.target.value)} />
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add</button>
              </form>
              <List items={state.tasks} empty="No tasks yet" render={(item) => `${item.status.replaceAll("_", " ")} · ${item.title}`} />
            </Panel>
          </section>
          <Panel title="Activity history">
            <Timeline items={state.timeline} emptyTitle="No request activity yet" />
          </Panel>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function detailSummary(category, details) {
  if (category === "mobility_assistance") {
    if (details.assessment_version === "v2_assessment_driven") {
      const tags = (details.passenger_context_tags || []).map((tag) => tag.replaceAll("_", " ")).join(", ")
      const assessment = details.functional_assessment || {}
      const ownDevice = details.own_mobility_device
      const ownDeviceDetails = details.own_device_details || {}
      const batteryDetails = details.battery_details || {}
      const parts = [
        tags ? `context: ${tags}` : null,
        `suggested: ${details.suggested_ssr_code || "manual_review"}`,
        details.suggested_ssr_reason ? `reason: ${details.suggested_ssr_reason}` : null,
        `confirmed: ${details.confirmed_ssr_code || details.suggested_ssr_code || "manual_review"}`,
        details.override_reason ? `override: ${details.override_reason}` : null,
      ].filter(Boolean)
      const assessmentSummary = Object.entries(assessment).filter(([, value]) => value && value !== "unknown").slice(0, 4).map(([key, value]) => `${key.replaceAll("_", " ")}: ${value}`).join("; ")
      if (assessmentSummary) parts.push(`assessment: ${assessmentSummary}`)
      if (ownDevice && ownDevice !== "no") {
        parts.push(`own device: ${String(ownDevice).replaceAll("_", " ")}`)
        const dimensions = [ownDeviceDetails.length_cm, ownDeviceDetails.width_cm, ownDeviceDetails.height_cm].filter(Boolean).join("×")
        if (ownDeviceDetails.weight_kg) parts.push(`${ownDeviceDetails.weight_kg} kg`)
        if (dimensions) parts.push(`${dimensions} cm`)
      }
      if (["electric_wheelchair_powerchair", "mobility_scooter"].includes(ownDevice)) {
        const battery = [batteryDetails.battery_type, batteryDetails.battery_watt_hours ? `${batteryDetails.battery_watt_hours} Wh` : null, batteryDetails.battery_removable ? `removable: ${batteryDetails.battery_removable}` : null].filter(Boolean).join(", ")
        if (battery) parts.push(`battery: ${battery.replaceAll("_", " ")}`)
      }
      return parts.join(" · ")
    }
    const legacyCode = details.assistance_code || details.wheelchair_type || "unknown"
    const ownDevice = details.own_mobility_device || (details.battery_wheelchair ? "electric wheelchair / powerchair" : "no")
    const parts = [`legacy assistance code: ${legacyCode}`]
    if (ownDevice && ownDevice !== "no") {
      parts.push(`own device: ${String(ownDevice).replaceAll("_", " ")}`)
      const dimensions = [details.length_cm, details.width_cm, details.height_cm].filter(Boolean).join("×")
      if (details.weight_kg) parts.push(`${details.weight_kg} kg`)
      if (dimensions) parts.push(`${dimensions} cm`)
    }
    if (["electric_wheelchair_powerchair", "mobility_scooter"].includes(details.own_mobility_device)) {
      const battery = [details.battery_type, details.battery_watt_hours ? `${details.battery_watt_hours} Wh` : null, details.battery_removable ? `removable: ${details.battery_removable}` : null].filter(Boolean).join(", ")
      if (battery) parts.push(`battery: ${battery.replaceAll("_", " ")}`)
    }
    return parts.join(" · ")
  }
  return Object.entries(details)
    .filter(([, value]) => value !== "" && value !== null && value !== undefined)
    .slice(0, 4)
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${String(value)}`)
    .join(" · ")
}

function Panel({ title, children }) {
  return (
    <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <h3 className="font-semibold text-slate-950">{title}</h3>
      </div>
      {children}
    </section>
  )
}

function List({ items, empty, render }) {
  if (!items?.length) return <EmptyState title={empty} body="Add records when the agency has the information." />
  return (
    <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200 bg-white">
      {items.map((item) => <div className="p-3 text-sm leading-6 text-slate-700" key={item.id}>{render(item)}</div>)}
    </div>
  )
}

function InfoCard({ title, rows }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <dl className="mt-4 space-y-3 text-sm">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt className="font-medium text-slate-700">{label}</dt>
            <dd className="mt-1 text-slate-600">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

function AirlineIntelLinkPanel({ title, airlineCode, serviceCodes }) {
  const primaryService = serviceCodes.find(Boolean)
  const query = new URLSearchParams()
  if (airlineCode) query.set("airline", airlineCode)
  if (primaryService) query.set("service_code", primaryService)
  const examples = ["PETC", "AVIH", "WCHR", "WCHS", "WCHC", "UMNR"]
  return (
    <section className="rounded-lg border border-blue-100 bg-blue-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-blue-950">{title}</h3>
          <p className="mt-1 text-sm text-blue-800">Decision support only. Open policy and service notes for manual review.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" href={`/agency/airline-intelligence?${query.toString()}`}>Open search</a>
          {examples.map((code) => <a className="rounded-md border border-blue-200 bg-white px-2 py-1 text-xs font-semibold text-blue-700" href={`/agency/airline-intelligence?service_code=${code}`} key={code}>{code}</a>)}
        </div>
      </div>
    </section>
  )
}
