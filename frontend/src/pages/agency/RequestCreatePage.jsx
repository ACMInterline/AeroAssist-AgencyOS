import { useEffect, useMemo, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const serviceCategories = [
  "mobility_assistance",
  "medical_travel",
  "pet_travel",
  "unaccompanied_minor",
  "child_travel_support",
  "special_baggage",
  "sports_equipment",
  "documents_visa",
  "booking_planning",
  "disruption_support",
  "refund_exchange",
  "claims_support",
  "airport_assistance",
  "other",
]

const assistanceCodes = {
  WCHR: "Can walk and use stairs; wheelchair needed for airport distance.",
  WCHS: "Can walk short distances; cannot use stairs.",
  WCHC: "Cannot walk; full assistance to/from aircraft seat.",
  meet_and_assist: "Meet and assist only; wheelchair may not be required.",
  unknown: "Needs staff assessment before confirming airline/airport handling.",
  to_be_assessed: "Needs staff assessment before confirming airline/airport handling.",
}

const triStateOptions = [["unknown", "Unknown"], ["yes", "Yes"], ["no", "No"]]
const ownMobilityDeviceOptions = [
  ["no", "No"],
  ["manual_wheelchair", "Manual wheelchair"],
  ["electric_wheelchair_powerchair", "Electric wheelchair / powerchair"],
  ["mobility_scooter", "Mobility scooter"],
  ["walker_rollator_crutches", "Walker / rollator / crutches"],
  ["other", "Other"],
  ["unknown", "Unknown"],
]
const batteryDeviceTypes = new Set(["electric_wheelchair_powerchair", "mobility_scooter"])

const blankPassenger = () => ({ passenger_id: "", first_name: "", last_name: "", display_name: "", date_of_birth: "", passenger_type: "adult", mobility_notes: "", medical_notes: "", notes: "" })
const blankSegment = () => ({ sequence: 1, origin_text: "", destination_text: "", departure_date: "", departure_time_window: "", arrival_date: "", arrival_time_window: "", marketing_airline: "", operating_airline: "", flight_number: "", cabin_preference: "", notes: "" })
const blankService = () => ({ category: "mobility_assistance", applies_to_all_passengers: true, applies_to_all_segments: true, passenger_ids: [], segment_ids: [], notes: "", details: { assistance_code: "unknown", own_mobility_device: "no" } })

export default function RequestCreatePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({
    client_mode: "existing",
    client_id: "",
    client_name: "",
    client_email: "",
    client_phone: "",
    client_organization: "",
    client_notes: "",
    title: "",
    status: "new",
    source: "staff_created",
    priority: "normal",
    trip_type: "unknown",
    origin: "",
    destination: "",
    departure_date: "",
    return_date: "",
    route_notes: "",
    internal_notes: "",
    client_visible_notes: "",
    passengers: [blankPassenger()],
    segments: [blankSegment()],
    services: [blankService()],
  })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const [clients, passengers] = await Promise.all([
        apiGet(`/api/agencies/${context.agency.id}/clients`),
        apiGet(`/api/agencies/${context.agency.id}/passengers`),
      ])
      setState({ ...context, clients: clients.items, passengers: passengers.items })
      setForm((current) => ({ ...current, client_id: clients.items[0]?.id || "" }))
    }
    load().catch((err) => setError(err.message))
  }, [])

  const derivedTitle = useMemo(() => {
    const client = form.client_mode === "existing" ? state?.clients?.find((item) => item.id === form.client_id)?.display_name : form.client_name
    const route = form.origin && form.destination ? `${form.origin} → ${form.destination}` : form.segments[0]?.origin_text && form.segments[0]?.destination_text ? `${form.segments[0].origin_text} → ${form.segments[0].destination_text}` : ""
    const service = form.services[0]?.category?.replaceAll("_", " ")
    return [client, route || service].filter(Boolean).join(" · ")
  }, [form, state])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  function updateArray(name, index, patch) {
    setForm((current) => ({ ...current, [name]: current[name].map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) }))
  }

  function addArrayItem(name, factory) {
    setForm((current) => ({ ...current, [name]: [...current[name], factory()] }))
  }

  function removeArrayItem(name, index) {
    setForm((current) => ({ ...current, [name]: current[name].filter((_, itemIndex) => itemIndex !== index) }))
  }

  function validate() {
    if (form.client_mode === "existing" && !form.client_id) return "Select a client or create one inline."
    if (form.client_mode === "inline" && (!form.client_name || (!form.client_email && !form.client_phone))) return "Inline client requires name and email or phone."
    if (!form.segments.some((segment) => segment.origin_text && segment.destination_text) && !(form.origin && form.destination)) return "Add at least one route segment or origin/destination."
    if (!form.services.length) return "Select at least one service category."
    return ""
  }

  async function submit(event) {
    event.preventDefault()
    setError("")
    const validation = validate()
    if (validation) {
      setError(validation)
      return
    }
    const payload = {
      client: form.client_mode === "existing" ? { client_id: form.client_id } : {
        name: form.client_name,
        email: form.client_email || undefined,
        phone: form.client_phone || undefined,
        organization: form.client_organization || undefined,
        notes: form.client_notes || undefined,
      },
      passengers: form.passengers.filter((passenger) => passenger.passenger_id || passenger.first_name || passenger.display_name).map(cleanObject),
      trip_type: form.trip_type,
      origin: form.origin || undefined,
      destination: form.destination || undefined,
      departure_date: form.departure_date || undefined,
      return_date: form.return_date || undefined,
      route_notes: form.route_notes || undefined,
      segments: form.segments.filter((segment) => segment.origin_text && segment.destination_text).map((segment, index) => cleanObject({ ...segment, sequence: Number(segment.sequence) || index + 1 })),
      services: form.services.map((service) => cleanObject({
        category: service.category,
        details: serviceDetails(service),
        applies_to_all_passengers: service.applies_to_all_passengers,
        applies_to_all_segments: service.applies_to_all_segments,
        notes: service.notes || undefined,
      })),
      title: form.title || derivedTitle || undefined,
      status: form.status,
      source: form.source,
      priority: form.priority,
      internal_notes: form.internal_notes || undefined,
      client_visible_notes: form.client_visible_notes || undefined,
    }
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/requests/builder`, payload)
      window.location.href = `/agency/requests/${result.request.id}`
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/agency/requests">Back to requests</a>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Operational Request Builder V1</h2>
            <p className="mt-1 text-sm text-slate-600">Build a structured assistance case with client, passengers, itinerary, services, and notes before offers or bookings exist.</p>
          </div>
          {error ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          <form className="space-y-5" onSubmit={submit}>
            <Section title="1. Client">
              <div className="flex gap-3 text-sm">
                <label><input type="radio" checked={form.client_mode === "existing"} onChange={() => setField("client_mode", "existing")} /> Existing client</label>
                <label><input type="radio" checked={form.client_mode === "inline"} onChange={() => setField("client_mode", "inline")} /> Create inline</label>
              </div>
              {form.client_mode === "existing" ? (
                <Select label="Client" value={form.client_id} onChange={(value) => setField("client_id", value)} options={(state?.clients || []).map((client) => [client.id, client.display_name])} required />
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  <Field label="Name" value={form.client_name} onChange={(value) => setField("client_name", value)} required />
                  <Field label="Email" type="email" value={form.client_email} onChange={(value) => setField("client_email", value)} />
                  <Field label="Phone" value={form.client_phone} onChange={(value) => setField("client_phone", value)} />
                  <Field label="Organization" value={form.client_organization} onChange={(value) => setField("client_organization", value)} />
                  <TextArea label="Client notes" value={form.client_notes} onChange={(value) => setField("client_notes", value)} />
                </div>
              )}
            </Section>

            <Section title="2. Passengers">
              {!form.passengers.some((passenger) => passenger.passenger_id || passenger.first_name || passenger.display_name) ? <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">No passengers yet. You can save with client-only context, but add at least one passenger when possible.</p> : null}
              {form.passengers.map((passenger, index) => (
                <div className="rounded-md border border-slate-100 p-3" key={index}>
                  <div className="grid gap-3 md:grid-cols-3">
                    <Select label="Existing passenger" value={passenger.passenger_id} onChange={(value) => updateArray("passengers", index, { passenger_id: value })} options={[["", "Create inline"], ...(state?.passengers || []).map((item) => [item.id, item.display_name])]} />
                    <Field label="First name" value={passenger.first_name} onChange={(value) => updateArray("passengers", index, { first_name: value })} />
                    <Field label="Display name" value={passenger.display_name} onChange={(value) => updateArray("passengers", index, { display_name: value })} />
                    <Field label="Last name" value={passenger.last_name} onChange={(value) => updateArray("passengers", index, { last_name: value })} />
                    <Field label="Date of birth" type="date" value={passenger.date_of_birth} onChange={(value) => updateArray("passengers", index, { date_of_birth: value })} />
                    <Select label="Passenger type" value={passenger.passenger_type} onChange={(value) => updateArray("passengers", index, { passenger_type: value })} options={["adult", "child", "infant", "senior", "unaccompanied_minor"].map((item) => [item, item.replaceAll("_", " ")])} />
                  </div>
                  <TextArea label="Mobility / medical / passenger notes" value={passenger.notes} onChange={(value) => updateArray("passengers", index, { notes: value, mobility_notes: value })} />
                  {form.passengers.length > 1 ? <button className="mt-2 text-sm font-medium text-rose-700" type="button" onClick={() => removeArrayItem("passengers", index)}>Remove passenger</button> : null}
                </div>
              ))}
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => addArrayItem("passengers", blankPassenger)}>Add passenger</button>
            </Section>

            <Section title="3. Itinerary / route">
              <div className="grid gap-3 md:grid-cols-4">
                <Select label="Trip type" value={form.trip_type} onChange={(value) => setField("trip_type", value)} options={["one_way", "round_trip", "multi_city", "unknown"].map((item) => [item, item.replaceAll("_", " ")])} />
                <Field label="Origin" value={form.origin} onChange={(value) => setField("origin", value)} />
                <Field label="Destination" value={form.destination} onChange={(value) => setField("destination", value)} />
                <Field label="Departure date" type="date" value={form.departure_date} onChange={(value) => setField("departure_date", value)} />
                <Field label="Return date" type="date" value={form.return_date} onChange={(value) => setField("return_date", value)} />
              </div>
              <TextArea label="Route notes" value={form.route_notes} onChange={(value) => setField("route_notes", value)} />
              {form.segments.map((segment, index) => (
                <div className="grid gap-3 rounded-md border border-slate-100 p-3 md:grid-cols-4" key={index}>
                  <Field label="Order" type="number" value={segment.sequence} onChange={(value) => updateArray("segments", index, { sequence: value })} />
                  <Field label="Origin" value={segment.origin_text} onChange={(value) => updateArray("segments", index, { origin_text: value })} required />
                  <Field label="Destination" value={segment.destination_text} onChange={(value) => updateArray("segments", index, { destination_text: value })} required />
                  <Field label="Departure date" type="date" value={segment.departure_date} onChange={(value) => updateArray("segments", index, { departure_date: value })} />
                  <Field label="Departure time" value={segment.departure_time_window} onChange={(value) => updateArray("segments", index, { departure_time_window: value })} />
                  <Field label="Arrival date" type="date" value={segment.arrival_date} onChange={(value) => updateArray("segments", index, { arrival_date: value })} />
                  <Field label="Marketing airline" value={segment.marketing_airline} onChange={(value) => updateArray("segments", index, { marketing_airline: value })} />
                  <Field label="Flight number" value={segment.flight_number} onChange={(value) => updateArray("segments", index, { flight_number: value })} />
                  <Field label="Cabin / class" value={segment.cabin_preference} onChange={(value) => updateArray("segments", index, { cabin_preference: value })} />
                  <TextArea label="Segment notes" value={segment.notes} onChange={(value) => updateArray("segments", index, { notes: value })} />
                  {form.segments.length > 1 ? <button className="text-sm font-medium text-rose-700" type="button" onClick={() => removeArrayItem("segments", index)}>Remove segment</button> : null}
                </div>
              ))}
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => addArrayItem("segments", () => ({ ...blankSegment(), sequence: form.segments.length + 1 }))}>Add segment</button>
            </Section>

            <Section title="4. Services">
              {form.services.map((service, index) => (
                <div className="rounded-md border border-slate-100 p-3" key={index}>
                  <div className="grid gap-3 md:grid-cols-3">
                    <Select label="Service category" value={service.category} onChange={(value) => updateArray("services", index, { category: value })} options={serviceCategories.map((item) => [item, item.replaceAll("_", " ")])} />
                    <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={service.applies_to_all_passengers} onChange={(event) => updateArray("services", index, { applies_to_all_passengers: event.target.checked })} /> All passengers</label>
                    <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={service.applies_to_all_segments} onChange={(event) => updateArray("services", index, { applies_to_all_segments: event.target.checked })} /> All segments</label>
                  </div>
                  <ConditionalServiceFields service={service} onChange={(patch) => updateArray("services", index, { details: { ...service.details, ...patch } })} />
                  <TextArea label={service.category === "mobility_assistance" ? "Additional mobility notes" : "Service notes"} value={service.notes} onChange={(value) => updateArray("services", index, { notes: value })} />
                  {form.services.length > 1 ? <button className="mt-2 text-sm font-medium text-rose-700" type="button" onClick={() => removeArrayItem("services", index)}>Remove service</button> : null}
                </div>
              ))}
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => addArrayItem("services", blankService)}>Add service</button>
            </Section>

            <Section title="5. Notes and summary">
              <div className="grid gap-3 md:grid-cols-3">
                <Select label="Status" value={form.status} onChange={(value) => setField("status", value)} options={["draft", "new", "triage"].map((item) => [item, item])} />
                <Select label="Priority" value={form.priority} onChange={(value) => setField("priority", value)} options={["low", "normal", "high", "urgent"].map((item) => [item, item])} />
                <Select label="Source" value={form.source} onChange={(value) => setField("source", value)} options={["staff_created", "phone", "email", "whatsapp", "walk_in", "public_website", "client_portal", "imported", "internal"].map((item) => [item, item.replaceAll("_", " ")])} />
              </div>
              <Field label="Operational title" value={form.title || derivedTitle} onChange={(value) => setField("title", value)} />
              <TextArea label="Internal notes" value={form.internal_notes} onChange={(value) => setField("internal_notes", value)} />
              <TextArea label="Client-visible notes" value={form.client_visible_notes} onChange={(value) => setField("client_visible_notes", value)} />
            </Section>

            <button className="rounded-md bg-blue-600 px-5 py-3 text-sm font-semibold text-white" type="submit">Create operational request</button>
          </form>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function serviceDetails(service) {
  return cleanObject(service.details || {})
}

function cleanObject(value) {
  return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== "" && item !== undefined && item !== null))
}

function Section({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function Field({ label, value, onChange, type = "text", required = false }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value} required={required} onChange={(event) => onChange(event.target.value)} /></label>
}

function TextArea({ label, value, onChange }) {
  return <label className="block text-sm font-medium text-slate-700 md:col-span-2">{label}<textarea className="mt-2 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, onChange, options, required = false }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} required={required} onChange={(event) => onChange(event.target.value)}>{options.map(([optionValue, labelText]) => <option key={optionValue} value={optionValue}>{labelText}</option>)}</select></label>
}

function ServiceCard({ title, body, children }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      <p className="mt-1 text-xs leading-5 text-slate-600">{body}</p>
      <div className="mt-3">{children}</div>
    </div>
  )
}

function ConditionalServiceFields({ service, onChange }) {
  const details = service.details || {}
  if (service.category === "mobility_assistance") {
    const assistanceCode = details.assistance_code || details.wheelchair_type || "unknown"
    const ownDevice = details.own_mobility_device || (details.battery_wheelchair ? "electric_wheelchair_powerchair" : "no")
    const showDeviceDetails = ownDevice && ownDevice !== "no"
    const showBatteryDetails = batteryDeviceTypes.has(ownDevice)
    return (
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <ServiceCard title="Assistance required" body="Choose the operational assistance code separately from any personal mobility device.">
          <Select
            label="Required assistance code"
            value={assistanceCode}
            onChange={(value) => onChange({ assistance_code: value })}
            options={[
              ["WCHR", "WCHR"],
              ["WCHS", "WCHS"],
              ["WCHC", "WCHC"],
              ["meet_and_assist", "MAAS / meet and assist"],
              ["unknown", "Unknown"],
              ["to_be_assessed", "To be assessed"],
            ]}
          />
          <p className="mt-2 rounded-md bg-blue-50 p-3 text-xs leading-5 text-blue-900">{assistanceCodes[assistanceCode] || assistanceCodes.unknown}</p>
        </ServiceCard>
        <ServiceCard title="Operational details" body="Optional clarifiers for edge cases; these do not replace the assistance code.">
          <div className="grid gap-3">
            <Select label="Can transfer to aircraft seat?" value={details.can_transfer_to_aircraft_seat || "unknown"} onChange={(value) => onChange({ can_transfer_to_aircraft_seat: value })} options={triStateOptions} />
            <Select label="Can walk short distance?" value={details.can_walk_short_distance || "unknown"} onChange={(value) => onChange({ can_walk_short_distance: value })} options={triStateOptions} />
            <Select label="Needs aisle chair?" value={details.needs_aisle_chair || "unknown"} onChange={(value) => onChange({ needs_aisle_chair: value })} options={triStateOptions} />
            <Select label="Needs lift/stair assistance?" value={details.needs_lift_or_stair_assistance || "unknown"} onChange={(value) => onChange({ needs_lift_or_stair_assistance: value })} options={triStateOptions} />
          </div>
        </ServiceCard>
        <ServiceCard title="Own mobility device" body="Capture personal device details only when the passenger travels with one.">
          <Select label="Travelling with own mobility device?" value={ownDevice} onChange={(value) => onChange({ own_mobility_device: value, device_type: value === "no" ? "" : value })} options={ownMobilityDeviceOptions} />
          {showDeviceDetails ? (
            <div className="mt-3 grid gap-3">
              <Field label="Brand / model" value={details.brand_model || ""} onChange={(value) => onChange({ brand_model: value })} />
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Weight kg" type="number" value={details.weight_kg || ""} onChange={(value) => onChange({ weight_kg: value })} />
                <Select label="Foldable / collapsible" value={details.foldable_or_collapsible || "unknown"} onChange={(value) => onChange({ foldable_or_collapsible: value })} options={triStateOptions} />
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <Field label="Length cm" type="number" value={details.length_cm || ""} onChange={(value) => onChange({ length_cm: value })} />
                <Field label="Width cm" type="number" value={details.width_cm || ""} onChange={(value) => onChange({ width_cm: value })} />
                <Field label="Height cm" type="number" value={details.height_cm || ""} onChange={(value) => onChange({ height_cm: value })} />
              </div>
              <Field label="Device notes" value={details.device_notes || ""} onChange={(value) => onChange({ device_notes: value })} />
            </div>
          ) : null}
          {showBatteryDetails ? (
            <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3">
              <p className="text-sm font-semibold text-amber-950">Battery details</p>
              <div className="mt-3 grid gap-3">
                <Select label="Battery type" value={details.battery_type || "unknown"} onChange={(value) => onChange({ battery_type: value })} options={[["dry_gel_sealed_lead_acid", "Dry / gel / sealed lead acid"], ["lithium_ion", "Lithium ion"], ["spillable_wet_cell", "Spillable wet cell"], ["unknown", "Unknown"]]} />
                <Select label="Battery removable?" value={details.battery_removable || "unknown"} onChange={(value) => onChange({ battery_removable: value })} options={triStateOptions} />
                <div className="grid gap-3 sm:grid-cols-3">
                  <Field label="Watt hours" type="number" value={details.battery_watt_hours || ""} onChange={(value) => onChange({ battery_watt_hours: value })} />
                  <Field label="Voltage" type="number" value={details.battery_voltage || ""} onChange={(value) => onChange({ battery_voltage: value })} />
                  <Field label="Amp hours" type="number" value={details.battery_amp_hours || ""} onChange={(value) => onChange({ battery_amp_hours: value })} />
                </div>
                <Select label="Spare battery carried?" value={details.spare_battery_carried || "unknown"} onChange={(value) => onChange({ spare_battery_carried: value })} options={triStateOptions} />
                <Select label="Battery documentation available?" value={details.battery_documentation_available || "unknown"} onChange={(value) => onChange({ battery_documentation_available: value })} options={triStateOptions} />
              </div>
            </div>
          ) : null}
        </ServiceCard>
      </div>
    )
  }
  if (service.category === "medical_travel") {
    return <div className="mt-3 grid gap-3 md:grid-cols-4"><Check label="Medical clearance" checked={details.medical_clearance_needed} onChange={(value) => onChange({ medical_clearance_needed: value })} /><Check label="Oxygen needed" checked={details.oxygen_needed} onChange={(value) => onChange({ oxygen_needed: value })} /><Check label="Stretcher needed" checked={details.stretcher_needed} onChange={(value) => onChange({ stretcher_needed: value })} /><Check label="Companion required" checked={details.companion_required} onChange={(value) => onChange({ companion_required: value })} /><Field label="Fit-to-fly status" value={details.fit_to_fly_status || ""} onChange={(value) => onChange({ fit_to_fly_status: value })} /></div>
  }
  if (service.category === "pet_travel") {
    return <div className="mt-3 grid gap-3 md:grid-cols-4"><Field label="Pet type" value={details.pet_type || ""} onChange={(value) => onChange({ pet_type: value })} /><Select label="Transport" value={details.transport || "unknown"} onChange={(value) => onChange({ transport: value })} options={["cabin", "hold", "manifest_cargo", "unknown"].map((item) => [item, item.replaceAll("_", " ")])} /><Field label="Weight" value={details.weight || ""} onChange={(value) => onChange({ weight: value })} /><Field label="Kennel dimensions" value={details.kennel_dimensions || ""} onChange={(value) => onChange({ kennel_dimensions: value })} /><Field label="Documents status" value={details.documents_status || ""} onChange={(value) => onChange({ documents_status: value })} /></div>
  }
  if (["unaccompanied_minor", "child_travel_support"].includes(service.category)) {
    return <div className="mt-3 grid gap-3 md:grid-cols-4"><Field label="Child age" value={details.child_age || ""} onChange={(value) => onChange({ child_age: value })} /><Check label="Escort needed" checked={details.escort_needed} onChange={(value) => onChange({ escort_needed: value })} /><Field label="Handover contact" value={details.handover_contact || ""} onChange={(value) => onChange({ handover_contact: value })} /><Field label="Pickup contact" value={details.pickup_contact || ""} onChange={(value) => onChange({ pickup_contact: value })} /><Check label="Airline UM service" checked={details.airline_um_service_required} onChange={(value) => onChange({ airline_um_service_required: value })} /></div>
  }
  if (["special_baggage", "sports_equipment"].includes(service.category)) {
    return <div className="mt-3 grid gap-3 md:grid-cols-4"><Field label="Item type" value={details.item_type || ""} onChange={(value) => onChange({ item_type: value })} /><Field label="Dimensions" value={details.dimensions || ""} onChange={(value) => onChange({ dimensions: value })} /><Field label="Weight" value={details.weight || ""} onChange={(value) => onChange({ weight: value })} /><Field label="Quantity" value={details.quantity || ""} onChange={(value) => onChange({ quantity: value })} /><Check label="Fragile / oversized" checked={details.fragile_oversized} onChange={(value) => onChange({ fragile_oversized: value })} /></div>
  }
  if (service.category === "documents_visa") {
    return <div className="mt-3 grid gap-3 md:grid-cols-4"><Field label="Nationality" value={details.nationality || ""} onChange={(value) => onChange({ nationality: value })} /><Field label="Residence" value={details.residence || ""} onChange={(value) => onChange({ residence: value })} /><Field label="Documents needed" value={details.destination_documents_needed || ""} onChange={(value) => onChange({ destination_documents_needed: value })} /><Field label="Visa/transit concern" value={details.visa_transit_concern || ""} onChange={(value) => onChange({ visa_transit_concern: value })} /></div>
  }
  if (["disruption_support", "refund_exchange", "claims_support"].includes(service.category)) {
    return <div className="mt-3 grid gap-3 md:grid-cols-4"><Field label="Booking reference" value={details.booking_reference || ""} onChange={(value) => onChange({ booking_reference: value })} /><Field label="Ticket number" value={details.ticket_number || ""} onChange={(value) => onChange({ ticket_number: value })} /><Field label="Disruption type" value={details.disruption_type || ""} onChange={(value) => onChange({ disruption_type: value })} /><Field label="Desired outcome" value={details.desired_outcome || ""} onChange={(value) => onChange({ desired_outcome: value })} /><Field label="Deadline" type="date" value={details.deadline || ""} onChange={(value) => onChange({ deadline: value })} /></div>
  }
  return <div className="mt-3 grid gap-3 md:grid-cols-2"><Field label="Details" value={details.summary || ""} onChange={(value) => onChange({ summary: value })} /></div>
}

function Check({ label, checked, onChange }) {
  return <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={Boolean(checked)} onChange={(event) => onChange(event.target.checked)} /> {label}</label>
}
