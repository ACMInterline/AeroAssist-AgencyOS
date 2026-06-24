import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import RequestStatusBadge from "../../components/RequestStatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function RequestDetailPage({ requestId }) {
  const [state, setState] = useState(null)
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

  const allowedRelationships = (state?.agencyRelationships || []).filter((relationship) => relationship.client_id === state?.request?.client_id && relationship.passenger_id === forms.passenger_id && relationship.status === "active")

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/requests">Back to requests</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state?.request?.request_reference}</p>
              <h2 className="text-3xl font-semibold tracking-tight text-slate-950">{state?.request?.title}</h2>
              <p className="mt-1 text-sm text-slate-600">Request is an inquiry/case. Intended segments are not booked services.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <RequestStatusBadge status={state?.request?.status} />
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/offers/new?requestId=${requestId}`}>
                Create offer
              </a>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" onClick={archiveOrRestore}>
                {state?.request?.status === "archived" ? "Restore" : "Archive"}
              </button>
            </div>
            </div>
          </div>
          <section className="grid gap-4 lg:grid-cols-3">
            <InfoCard title="Overview" rows={[
              ["Client", state?.client?.display_name],
              ["Priority", state?.request?.priority],
              ["Source", state?.request?.source?.replaceAll("_", " ")],
              ["Route", state?.request?.route_summary || "Not set"],
              ["Passengers", state?.request?.passenger_count ?? 0],
              ["Pets", state?.request?.pet_count ?? 0],
              ["Special services", state?.request?.special_service_count ?? 0],
              ["Trip type", state?.request?.trip_type?.replaceAll("_", " ") || "unknown"],
              ["Services", state?.request?.service_summary || "Not set"],
              ["Source intake", state?.request?.source_intake_id ? <a className="text-blue-700 underline" href={`/agency/request-intakes/${state.request.source_intake_id}`}>Open intake</a> : "None"],
            ]} />
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
              <p className="mt-3 text-sm text-slate-600">Offer creation comes next and is intentionally not active here.</p>
            </div>
            <InfoCard title="Notes" rows={[
              ["Client notes", state?.request?.client_notes || "None"],
              ["Internal notes", state?.request?.internal_notes || "None"],
              ["Client-visible", state?.request?.client_visible_notes || "None"],
            ]} />
          </section>
          <AirlineIntelLinkPanel
            title="Search Airline Intelligence"
            airlineCode={state.segments.find((segment) => segment.preferred_airline_code)?.preferred_airline_code}
            serviceCodes={state.services.map((service) => service.service_code)}
          />
          <Panel title="Case flags">
            <List items={state.case_flags} empty="No derived case flags yet" render={(item) => `${item.flag_label} · ${item.severity} · ${item.source}`} />
          </Panel>
          <Panel title="Passengers">
            <form className="grid gap-3 md:grid-cols-[1fr_1fr_auto]" onSubmit={addPassenger}>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.passenger_id} onChange={(event) => setField("passenger_id", event.target.value)}>
                {state.agencyPassengers.map((passenger) => <option key={passenger.id} value={passenger.id}>{passenger.display_name}</option>)}
              </select>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.relationship_id} onChange={(event) => setField("relationship_id", event.target.value)}>
                <option value="">No relationship selected</option>
                {allowedRelationships.map((relationship) => <option key={relationship.id} value={relationship.id}>{relationship.relationship_type.replaceAll("_", " ")}</option>)}
              </select>
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add passenger</button>
            </form>
            <List items={state.passengers} empty="No passengers linked yet" render={(item) => `${item.snapshot_display_name} · ${item.snapshot_passenger_type} · ${item.role_in_request.replaceAll("_", " ")}`} />
          </Panel>
          <Panel title="Intended itinerary">
            <form className="grid gap-3 md:grid-cols-[80px_1fr_1fr_auto]" onSubmit={addSegment}>
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" type="number" value={forms.sequence} onChange={(event) => setField("sequence", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Origin" value={forms.origin_text} onChange={(event) => setField("origin_text", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Destination" value={forms.destination_text} onChange={(event) => setField("destination_text", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add segment</button>
            </form>
            <List items={state.segments} empty="No intended segments yet" render={(item) => `${item.sequence}. ${item.origin_text} to ${item.destination_text}${item.departure_date ? ` · ${item.departure_date}` : ""}${item.preferred_flight_number ? ` · ${item.preferred_flight_number}` : ""}${item.cabin_preference ? ` · ${item.cabin_preference}` : ""}`} />
          </Panel>
          <Panel title="Requested services">
            <form className="grid gap-3 md:grid-cols-[120px_1fr_1fr_auto]" onSubmit={addService}>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Code" value={forms.service_code} onChange={(event) => setField("service_code", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Service name" value={forms.service_name} onChange={(event) => setField("service_name", event.target.value)} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Category" value={forms.service_category} onChange={(event) => setField("service_category", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add service</button>
            </form>
            <List items={state.services} empty="No services requested yet" render={(item) => `${item.service_code} · ${item.service_name} · ${item.status.replaceAll("_", " ")}${item.detail_payload && Object.keys(item.detail_payload).length ? ` · ${detailSummary(item.service_category, item.detail_payload)}` : ""}`} />
          </Panel>
          <Panel title="Passenger-segment services">
            <List items={state.passenger_segment_services} empty="No normalized passenger-segment services yet" render={(item) => {
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
          <Panel title="Source payload / snapshot">
            {Object.keys(state.request?.builder_payload_snapshot || {}).length ? <pre className="overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(state.request.builder_payload_snapshot, null, 2)}</pre> : state.request?.intake_payload_snapshot ? <pre className="overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(state.request.intake_payload_snapshot, null, 2)}</pre> : <EmptyState title="No source snapshot" body="Legacy requests may not have a builder or intake snapshot." />}
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
          <Panel title="Timeline">
            <List items={state.timeline} empty="No timeline events yet" render={(item) => `${item.title}${item.summary ? ` · ${item.summary}` : ""}`} />
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
