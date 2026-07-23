import { useState } from "react"
import PublicLayout from "../../layouts/PublicLayout"
import { apiPost } from "../../lib/api"

const isProduction = import.meta.env.PROD || import.meta.env.VITE_APP_ENV === "production"

export default function HomePage() {
  return (
    <PublicLayout>
      <section className="grid gap-6 md:grid-cols-[1.4fr_1fr] md:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Phase 1 Foundation</p>
          <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-normal text-slate-950 md:text-5xl">
            AeroAssist AgencyOS
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
            Multi-tenant operating platform foundation for micro and small travel agencies.
            This build establishes platform identity, agency workspace setup, roles, reference
            data, and tenant-aware API scaffolding.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href="/login">
              {isProduction ? "Sign in" : "Open demo login"}
            </a>
            <a className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800" href="/platform">
              View platform foundation
            </a>
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-base font-semibold text-slate-950">Implemented layers</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>AeroAssist Global / Platform Owner foundation</li>
            <li>Agency Workspace identity and settings foundation</li>
            <li>Global reference data seed layer</li>
            <li>Audit event scaffolding</li>
          </ul>
        </div>
      </section>
      <PublicRequestForm />
    </PublicLayout>
  )
}

function PublicRequestForm() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    origin: "",
    destination: "",
    departure_date: "",
    return_date: "",
    passenger_count: 1,
    service: "booking_or_planning",
    details: "",
    pet_transport: "PETC",
    pet_species: "",
    pet_weight_kg: "",
    container_weight_kg: "",
    carrier_length_cm: "",
    carrier_width_cm: "",
    carrier_height_cm: "",
    special_item_category: "other",
    special_item_name: "",
    special_item_weight_kg: "",
    privacy_policy_accepted: false,
  })
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState("")

  async function submit(event) {
    event.preventDefault()
    setError("")
    try {
      const [firstName, ...lastNameParts] = form.name.trim().split(/\s+/)
      const lastName = lastNameParts.join(" ")
      if (!lastName) throw new Error("Enter both first and last name.")
      const serviceKey = publicServiceKey(form.service)
      const passengerCount = Math.max(1, Number(form.passenger_count) || 1)
      const passengerLocalIds = Array.from({ length: passengerCount }, (_, index) => `pax_${index + 1}`)
      const segmentLocalId = "seg_1"
      const specialItem = form.service === "special_baggage" ? {
        item_local_id: "item_1",
        linked_passenger_local_id: passengerLocalIds[0],
        segment_scope_mode: "all_segments",
        segment_ids: [],
        item_category: form.special_item_category,
        details: publicSpecialItemDetails(form),
      } : null
      const detail = publicServiceDetails(serviceKey, form, specialItem)
      const result = await apiPost("/api/public/requests?privacy_policy_accepted=true", {
        request_version: 4,
        contact: {
          first_name: firstName,
          last_name: lastName,
          email: form.email,
          phone: form.phone || null,
        },
        trip: {
          trip_label: `${form.origin} to ${form.destination}`,
          trip_purpose: "leisure",
          quote_mode: form.return_date ? "round_trip" : "one_way",
          preferred_cabin: "Y",
        },
        itinerary_segments: [{
          segment_local_id: segmentLocalId,
          segment_order: 1,
          origin_label: form.origin,
          origin_iata: /^[A-Za-z]{3}$/.test(form.origin.trim()) ? form.origin.trim().toUpperCase() : "",
          destination_label: form.destination,
          destination_iata: /^[A-Za-z]{3}$/.test(form.destination.trim()) ? form.destination.trim().toUpperCase() : "",
          departure_date: form.departure_date,
          cabin: "Y",
        }],
        passengers: passengerLocalIds.map((passengerLocalId, index) => ({
          passenger_local_id: passengerLocalId,
          identity_status: "unresolved",
          passenger_type_code: "ADT",
          passenger_type_label: "Adult",
          first_name: index === 0 ? firstName : "",
          last_name: index === 0 ? lastName : "",
          selected_services: serviceKey ? [serviceKey] : [],
          service_details: serviceKey ? { [serviceKey]: detail } : {},
        })),
        pets: form.service === "pet_travel" ? [{
          pet_local_id: "pet_1",
          linked_passenger_local_id: passengerLocalIds[0],
          segment_scope_mode: "all_segments",
          segment_ids: [],
          pet_category: form.pet_transport,
          species_label: form.pet_species,
          pet_weight_kg: Number(form.pet_weight_kg),
          container_weight_kg: Number(form.container_weight_kg),
          carrier_length_cm: Number(form.carrier_length_cm),
          carrier_width_cm: Number(form.carrier_width_cm),
          carrier_height_cm: Number(form.carrier_height_cm),
          special_instructions: form.details,
        }] : [],
        special_items: specialItem ? [specialItem] : [],
        request_level_notes: form.details,
        admin_metadata: {
          source: "public_submission",
          status: "new",
          priority: "normal",
        },
      })
      setSuccess(result.intake)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="mt-10 rounded-lg border border-slate-200 bg-white p-6">
      <div className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Request assistance</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-950">Tell us what you need</h2>
        <p className="mt-2 text-sm text-slate-600">We received your request as an intake first. Our team reviews it before creating any operational case.</p>
      </div>
      {success ? (
        <div className="mt-5 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          We received your request. Our team will review it. Reference: <span className="font-semibold">{success.reference_code}</span>
        </div>
      ) : (
        <form className="mt-5 grid gap-4 md:grid-cols-2" onSubmit={submit}>
          <Field label="Name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} required />
          <Field label="Email" type="email" value={form.email} onChange={(value) => setForm({ ...form, email: value })} required />
          <Field label="Phone" value={form.phone} onChange={(value) => setForm({ ...form, phone: value })} />
          <Field label="Origin" value={form.origin} onChange={(value) => setForm({ ...form, origin: value })} required />
          <Field label="Destination" value={form.destination} onChange={(value) => setForm({ ...form, destination: value })} required />
          <Field label="Departure date" type="date" value={form.departure_date} onChange={(value) => setForm({ ...form, departure_date: value })} required />
          <Field label="Return date" type="date" value={form.return_date} onChange={(value) => setForm({ ...form, return_date: value })} />
          <Field label="Passengers" type="number" value={form.passenger_count} onChange={(value) => setForm({ ...form, passenger_count: value })} />
          <label className="block text-sm font-medium text-slate-700">Service type<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.service} onChange={(event) => setForm({ ...form, service: event.target.value })}>{["booking_or_planning", "mobility_assistance", "medical_travel", "pet_travel", "child_or_unaccompanied_minor", "special_baggage", "documents_or_visa", "disruption_or_claims", "other"].map((item) => <option value={item} key={item}>{item.replaceAll("_", " ")}</option>)}</select></label>
          {form.service === "pet_travel" ? (
            <div className="grid gap-4 rounded-md border border-slate-200 p-4 md:col-span-2 md:grid-cols-3">
              <label className="block text-sm font-medium text-slate-700">Travel arrangement<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.pet_transport} onChange={(event) => setForm({ ...form, pet_transport: event.target.value })}><option value="PETC">In cabin</option><option value="AVIH">In hold</option><option value="SVAN">Service animal</option><option value="OTHER">Not sure</option></select></label>
              <Field label="Animal species" value={form.pet_species} onChange={(value) => setForm({ ...form, pet_species: value })} required />
              <Field label="Animal weight kg" type="number" value={form.pet_weight_kg} onChange={(value) => setForm({ ...form, pet_weight_kg: value })} required />
              <Field label="Carrier weight kg" type="number" value={form.container_weight_kg} onChange={(value) => setForm({ ...form, container_weight_kg: value })} required />
              <Field label="Carrier length cm" type="number" value={form.carrier_length_cm} onChange={(value) => setForm({ ...form, carrier_length_cm: value })} required />
              <Field label="Carrier width cm" type="number" value={form.carrier_width_cm} onChange={(value) => setForm({ ...form, carrier_width_cm: value })} required />
              <Field label="Carrier height cm" type="number" value={form.carrier_height_cm} onChange={(value) => setForm({ ...form, carrier_height_cm: value })} required />
            </div>
          ) : null}
          {form.service === "special_baggage" ? (
            <div className="grid gap-4 rounded-md border border-slate-200 p-4 md:col-span-2 md:grid-cols-3">
              <label className="block text-sm font-medium text-slate-700">Item type<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.special_item_category} onChange={(event) => setForm({ ...form, special_item_category: event.target.value })}><option value="sports_equipment">Sports equipment</option><option value="musical_instrument">Musical instrument</option><option value="valuables_fragile">Valuable or fragile item</option><option value="other">Other</option></select></label>
              <Field label="Item name" value={form.special_item_name} onChange={(value) => setForm({ ...form, special_item_name: value })} required />
              <Field label="Weight kg" type="number" value={form.special_item_weight_kg} onChange={(value) => setForm({ ...form, special_item_weight_kg: value })} />
            </div>
          ) : null}
          <label className="block text-sm font-medium text-slate-700 md:col-span-2">Travel/request details<textarea className="mt-2 min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.details} required onChange={(event) => setForm({ ...form, details: event.target.value })} /></label>
          <label className="flex gap-2 text-sm text-slate-700 md:col-span-2"><input type="checkbox" checked={form.privacy_policy_accepted} onChange={(event) => setForm({ ...form, privacy_policy_accepted: event.target.checked })} required /> I consent to AeroAssist reviewing this request and contacting me about it.</label>
          {error ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800 md:col-span-2">{error}</p> : null}
          <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white md:w-fit" type="submit">Submit request</button>
        </form>
      )}
    </section>
  )
}

function publicServiceKey(value) {
  return {
    mobility_assistance: "wheelchair_and_mobility_assistance",
    medical_travel: "medical_equipment_and_travel_support",
    child_or_unaccompanied_minor: "children_traveling_alone",
    special_baggage: "special_items_and_equipment",
    documents_or_visa: "documents_and_travel_compliance",
    booking_or_planning: "documents_and_travel_compliance",
    disruption_or_claims: "documents_and_travel_compliance",
    other: "documents_and_travel_compliance",
  }[value] || null
}

function publicServiceDetails(serviceKey, form, specialItem) {
  const scope = { segment_scope_mode: "all_segments", segment_ids: [] }
  if (serviceKey === "wheelchair_and_mobility_assistance") {
    return { ...scope, suggested_ssr_code: "manual_review", confirmed_ssr_code: "manual_review", final_assistance_label: "Assessment required", notes: form.details }
  }
  if (serviceKey === "medical_equipment_and_travel_support") {
    return { ...scope, medical_clearance_needed: true, fit_to_fly_status: "unknown", notes: form.details }
  }
  if (serviceKey === "children_traveling_alone") {
    return { ...scope, airline_um_service_required: false, notes: form.details }
  }
  if (serviceKey === "special_items_and_equipment") {
    return { ...scope, item_local_ids: specialItem ? [specialItem.item_local_id] : [], item_type: form.special_item_name, quantity: 1, notes: form.details }
  }
  return { ...scope, destination_documents_needed: [], notes: form.details }
}

function publicSpecialItemDetails(form) {
  const details = {
    quantity: 1,
    ...(form.special_item_weight_kg ? { weight_kg: Number(form.special_item_weight_kg) } : {}),
    notes: form.details,
  }
  if (form.special_item_category === "sports_equipment") details.equipment_type = form.special_item_name
  else if (form.special_item_category === "musical_instrument") details.instrument_type = form.special_item_name
  else details.item_type = form.special_item_name
  return details
}

function Field({ label, value, onChange, type = "text", required = false }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value} required={required} onChange={(event) => onChange(event.target.value)} /></label>
}
