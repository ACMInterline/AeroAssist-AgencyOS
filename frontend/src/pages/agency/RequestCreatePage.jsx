import { useEffect, useMemo, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"
import { fetchAgencyFormProfiles, fetchEffectiveAgencyFormProfile } from "../../lib/formProfiles"
import { fetchReferenceDomain, fetchServiceCatalogue } from "../../lib/referenceData"

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

const triStateOptions = [["unknown", "Unknown"], ["yes", "Yes"], ["no", "No"]]
const ssrCodeOptions = [["use_suggested", "Use suggested"], ["WCHR", "WCHR"], ["WCHS", "WCHS"], ["WCHC", "WCHC"], ["MAAS", "MAAS"], ["MEDA", "MEDA"], ["BLND", "BLND"], ["DEAF", "DEAF"], ["OTHER", "OTHER"], ["manual_review", "Manual review"]]
const contextTagOptions = [
  ["prm", "PRM / reduced mobility"],
  ["src", "SRC / senior citizen"],
  ["temporary_injury", "Temporary injury"],
  ["medical_condition", "Medical condition"],
  ["blind_visual_impairment", "Blind or visually impaired"],
  ["deaf_hard_of_hearing", "Deaf or hard of hearing"],
  ["cognitive_neurodivergent", "Cognitive / neurodivergent assistance"],
  ["pregnancy", "Pregnancy"],
  ["child_young_passenger", "Child / young passenger support"],
  ["unaccompanied_minor", "Unaccompanied minor"],
  ["other", "Other"],
]
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
const blankService = () => ({ category: "mobility_assistance", applies_to_all_passengers: true, applies_to_all_segments: true, passenger_ids: [], segment_ids: [], notes: "", details: { assessment_version: "v2_assessment_driven", passenger_context_tags: [], functional_assessment: {}, confirmed_ssr_code: "use_suggested", own_mobility_device: "no", own_device_details: {}, battery_details: {} } })
const blankPet = () => ({ pet_name: "", species: "dog", breed: "", breed_free_text: "", requested_transport_mode: "petc", pet_weight_kg: "", container_weight_kg: "", combined_weight_kg: "", documentation_status: "pending_information", segment_keys: ["1"], notes: "" })
const blankSpecialItem = () => ({ item_category_code: "other", item_name: "", description: "", quantity: 1, weight_kg: "", transport_location: "checked_baggage", documentation_status: "pending_information", segment_keys: ["1"], notes: "" })

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
    agency_custom_fields: {},
    passengers: [blankPassenger()],
    segments: [blankSegment()],
    services: [blankService()],
    pets: [],
    special_items: [],
  })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const [clients, passengers, serviceCatalogue, petSpecies, specialItemCategories] = await Promise.all([
        apiGet(`/api/agencies/${context.agency.id}/clients`),
        apiGet(`/api/agencies/${context.agency.id}/passengers`),
        fetchServiceCatalogue().catch(() => ({ items: [] })),
        fetchReferenceDomain("pet_species").catch(() => ({ items: [] })),
        fetchReferenceDomain("special_item_categories").catch(() => ({ items: [] })),
      ])
      const profileList = await fetchAgencyFormProfiles(context.agency.id).catch(() => ({ items: [] }))
      const adminProfile = (profileList.items || []).find((profile) => profile.form_context === "admin_request" && profile.is_default) || (profileList.items || []).find((profile) => profile.form_context === "admin_request")
      const formProfile = adminProfile ? await fetchEffectiveAgencyFormProfile(context.agency.id, adminProfile.id).catch(() => null) : null
      setState({ ...context, clients: clients.items, passengers: passengers.items, serviceCatalogue: serviceCatalogue.items || [], petSpecies: petSpecies.items || [], specialItemCategories: specialItemCategories.items || [], formProfile })
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

  function fieldVisible(fieldKey, fallback = true) {
    const profile = state?.formProfile
    if (!profile || profile.fallback) return fallback
    const field = (profile.fields || []).find((item) => item.field_key === fieldKey)
    return field ? field.visible !== false : fallback
  }

  const customFields = (state?.formProfile?.fields || []).filter((field) => field.custom_field && field.visible)

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
    if (form.services.some((service) => !service.applies_to_all_segments && !service.segment_ids.length)) return "Every service must be assigned to at least one exact segment."
    if (form.services.some((service) => !service.applies_to_all_passengers && !service.passenger_ids.length)) return "Every service must be assigned to at least one exact passenger."
    const mobilityOverrideMissingReason = form.services.some((service) => {
      if (service.category !== "mobility_assistance") return false
      const recommendation = recommendMobilitySsr(service.details || {})
      const confirmed = service.details?.confirmed_ssr_code === "use_suggested" ? recommendation.code : service.details?.confirmed_ssr_code || recommendation.code
      return confirmed !== recommendation.code && !service.details?.override_reason
    })
    if (mobilityOverrideMissingReason) return "Mobility SSR overrides require an override reason."
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
      passengers: form.passengers.filter((passenger) => passenger.passenger_id || passenger.first_name || passenger.display_name || passenger.passenger_link_mode === "unresolved").map((passenger, index) => cleanObject({ ...passenger, request_passenger_key: `inline-${index}`, passenger_link_mode: passenger.passenger_id ? "existing" : (passenger.first_name || passenger.display_name ? "new_inline" : "unresolved") })),
      trip_type: form.trip_type,
      origin: form.origin || undefined,
      destination: form.destination || undefined,
      departure_date: form.departure_date || undefined,
      return_date: form.return_date || undefined,
      route_notes: form.route_notes || undefined,
      segments: form.segments.filter((segment) => segment.origin_text && segment.destination_text).map((segment, index) => cleanObject({ ...segment, segment_key: String(Number(segment.sequence) || index + 1), sequence: Number(segment.sequence) || index + 1 })),
      services: form.services.map((service) => cleanObject({
        category: service.category,
        service_code: service.service_code || undefined,
        service_catalogue_id: service.service_catalogue_id || undefined,
        service_family_code: service.service_family_code || undefined,
        details: serviceDetails(service),
        applies_to_all_passengers: service.applies_to_all_passengers,
        applies_to_all_segments: service.applies_to_all_segments,
        passenger_ids: service.applies_to_all_passengers ? [] : service.passenger_ids,
        segment_ids: service.applies_to_all_segments ? [] : service.segment_ids,
        notes: service.notes || undefined,
      })),
      pets: form.pets.map((pet, index) => {
        const { segment_keys, ...petPayload } = pet
        return cleanObject({
          pet_key: `pet-${index}`,
          ...petPayload,
          pet_weight_kg: numericOrUndefined(pet.pet_weight_kg),
          container_weight_kg: numericOrUndefined(pet.container_weight_kg),
          combined_weight_kg: numericOrUndefined(pet.combined_weight_kg),
          segment_transports: (segment_keys || []).map((key) => ({ segment_key: key, requested_transport_mode: pet.requested_transport_mode })),
        })
      }),
      special_items: form.special_items.map((item, index) => {
        const { segment_keys, ...itemPayload } = item
        return cleanObject({
          item_key: `item-${index}`,
          ...itemPayload,
          quantity: Number(item.quantity || 1),
          weight_kg: numericOrUndefined(item.weight_kg),
          segment_transports: (segment_keys || []).map((key) => ({ segment_key: key, transport_location: item.transport_location })),
        })
      }),
      title: form.title || derivedTitle || undefined,
      status: form.status,
      source: form.source,
      priority: form.priority,
      internal_notes: form.internal_notes || undefined,
      client_visible_notes: form.client_visible_notes || undefined,
      agency_custom_fields: form.agency_custom_fields,
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
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <a className="text-sm font-medium text-blue-700" href="/agency/requests">Back to requests</a>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Operational Request Builder V1</h2>
            <p className="mt-1 text-sm text-slate-600">Build a structured assistance case with client, passengers, itinerary, services, and notes before offers or bookings exist.</p>
          </div>
          {error ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          <div className="grid gap-6 xl:grid-cols-[220px_1fr]">
            <aside className="hidden xl:block">
              <div className="sticky top-24 rounded-lg border border-slate-200 bg-white p-3">
                {["Client", "Passengers", "Itinerary", "Services", "Pets", "Special items", "Summary"].map((item, index) => (
                  <a className="block rounded-md px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100" href={`#builder-${index + 1}`} key={item}>{index + 1}. {item}</a>
                ))}
              </div>
            </aside>
          <form className="space-y-5" onSubmit={submit}>
            <Section id="builder-1" eyebrow="Client context" title="1. Client">
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

            <Section id="builder-2" eyebrow="Travelers" title="2. Passengers">
              {!form.passengers.some((passenger) => passenger.passenger_id || passenger.first_name || passenger.display_name) ? <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">No passengers yet. You can save with client-only context, but add at least one passenger when possible.</p> : null}
              {form.passengers.map((passenger, index) => (
                <div className="rounded-md border border-slate-100 p-3" key={index}>
                  <div className="grid gap-3 md:grid-cols-3">
                    <Select label="Existing passenger" value={passenger.passenger_id} onChange={(value) => updateArray("passengers", index, { passenger_id: value })} options={[["", "Create inline"], ...(state?.passengers || []).map((item) => [item.id, item.display_name])]} />
                    <Field label="First name" value={passenger.first_name} onChange={(value) => updateArray("passengers", index, { first_name: value })} />
                    <Field label="Display name" value={passenger.display_name} onChange={(value) => updateArray("passengers", index, { display_name: value })} />
                    <Field label="Last name" value={passenger.last_name} onChange={(value) => updateArray("passengers", index, { last_name: value })} />
                    {fieldVisible("passengers.date_of_birth") ? <Field label="Date of birth" type="date" value={passenger.date_of_birth} onChange={(value) => updateArray("passengers", index, { date_of_birth: value })} /> : null}
                    {fieldVisible("passengers.passenger_type") ? <Select label="Passenger type" value={passenger.passenger_type} onChange={(value) => updateArray("passengers", index, { passenger_type: value })} options={["adult", "child", "infant", "senior", "unaccompanied_minor"].map((item) => [item, item.replaceAll("_", " ")])} /> : null}
                  </div>
                  <TextArea label="Mobility / medical / passenger notes" value={passenger.notes} onChange={(value) => updateArray("passengers", index, { notes: value, mobility_notes: value })} />
                  {form.passengers.length > 1 ? <button className="mt-2 text-sm font-medium text-rose-700" type="button" onClick={() => removeArrayItem("passengers", index)}>Remove passenger</button> : null}
                </div>
              ))}
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => addArrayItem("passengers", blankPassenger)}>Add passenger</button>
            </Section>

            <Section id="builder-3" eyebrow="Trip shape" title="3. Itinerary / route">
              <div className="grid gap-3 md:grid-cols-4">
                <Select label="Trip type" value={form.trip_type} onChange={(value) => setField("trip_type", value)} options={["one_way", "round_trip", "multi_city", "unknown"].map((item) => [item, item.replaceAll("_", " ")])} />
                <Field label="Origin" value={form.origin} onChange={(value) => setField("origin", value)} />
                <Field label="Destination" value={form.destination} onChange={(value) => setField("destination", value)} />
                <Field label="Departure date" type="date" value={form.departure_date} onChange={(value) => setField("departure_date", value)} />
                {fieldVisible("itinerary_segments.arrival_date") ? <Field label="Return date" type="date" value={form.return_date} onChange={(value) => setField("return_date", value)} /> : null}
              </div>
              {fieldVisible("itinerary_segments.notes") ? <TextArea label="Route notes" value={form.route_notes} onChange={(value) => setField("route_notes", value)} /> : null}
              {form.segments.map((segment, index) => (
                <div className="grid gap-3 rounded-md border border-slate-100 p-3 md:grid-cols-4" key={index}>
                  <Field label="Order" type="number" value={segment.sequence} onChange={(value) => updateArray("segments", index, { sequence: value })} />
                  <Field label="Origin" value={segment.origin_text} onChange={(value) => updateArray("segments", index, { origin_text: value })} required />
                  <Field label="Destination" value={segment.destination_text} onChange={(value) => updateArray("segments", index, { destination_text: value })} required />
                  <Field label="Departure date" type="date" value={segment.departure_date} onChange={(value) => updateArray("segments", index, { departure_date: value })} />
                  <Field label="Departure time" value={segment.departure_time_window} onChange={(value) => updateArray("segments", index, { departure_time_window: value })} />
                  {fieldVisible("itinerary_segments.arrival_date") ? <Field label="Arrival date" type="date" value={segment.arrival_date} onChange={(value) => updateArray("segments", index, { arrival_date: value })} /> : null}
                  {fieldVisible("itinerary_segments.preferred_airline") ? <Field label="Marketing airline" value={segment.marketing_airline} onChange={(value) => updateArray("segments", index, { marketing_airline: value })} /> : null}
                  <Field label="Flight number" value={segment.flight_number} onChange={(value) => updateArray("segments", index, { flight_number: value })} />
                  {fieldVisible("itinerary_segments.cabin_class") ? <Field label="Cabin / class" value={segment.cabin_preference} onChange={(value) => updateArray("segments", index, { cabin_preference: value })} /> : null}
                  {fieldVisible("itinerary_segments.notes") ? <TextArea label="Segment notes" value={segment.notes} onChange={(value) => updateArray("segments", index, { notes: value })} /> : null}
                  {form.segments.length > 1 ? <button className="text-sm font-medium text-rose-700" type="button" onClick={() => removeArrayItem("segments", index)}>Remove segment</button> : null}
                </div>
              ))}
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => addArrayItem("segments", () => ({ ...blankSegment(), sequence: form.segments.length + 1 }))}>Add segment</button>
            </Section>

            <Section id="builder-4" eyebrow="Assistance needs" title="4. Services">
              {form.services.map((service, index) => (
                <div className="rounded-md border border-slate-100 p-3" key={index}>
                  <div className="grid gap-3 md:grid-cols-3">
                    <Select label="Service catalogue" value={service.service_catalogue_id || ""} onChange={(value) => {
                      const selected = (state?.serviceCatalogue || []).find((item) => item.id === value)
                      updateArray("services", index, { service_catalogue_id: value, service_code: selected?.service_code || "", service_family_code: selected?.service_family_code || service.service_family_code, category: familyToCategory(selected?.service_family_code) || service.category })
                    }} options={[["", "Manual category"], ...(state?.serviceCatalogue || []).map((item) => [item.id, `${item.service_code} · ${item.service_label}`])]} />
                    <Select label="Service category" value={service.category} onChange={(value) => updateArray("services", index, { category: value, service_family_code: categoryToFamily(value) })} options={serviceCategories.map((item) => [item, item.replaceAll("_", " ")])} />
                    <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={service.applies_to_all_passengers} onChange={(event) => updateArray("services", index, { applies_to_all_passengers: event.target.checked })} /> All passengers</label>
                    <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={service.applies_to_all_segments} onChange={(event) => updateArray("services", index, { applies_to_all_segments: event.target.checked })} /> All segments</label>
                  </div>
                  {!service.applies_to_all_passengers ? <CheckboxGroup title="Assign to passengers" values={passengerKeys(form.passengers)} selected={service.passenger_ids} onToggle={(value) => updateArray("services", index, { passenger_ids: toggleValue(service.passenger_ids, value) })} /> : null}
                  {!service.applies_to_all_segments ? <CheckboxGroup title="Assign to segments" values={segmentKeys(form.segments)} selected={service.segment_ids} onToggle={(value) => updateArray("services", index, { segment_ids: toggleValue(service.segment_ids, value) })} /> : null}
                  <ConditionalServiceFields service={service} onChange={(patch) => updateArray("services", index, { details: { ...service.details, ...patch } })} />
                  <TextArea label={service.category === "mobility_assistance" ? "Additional mobility notes" : "Service notes"} value={service.notes} onChange={(value) => updateArray("services", index, { notes: value })} />
                  {form.services.length > 1 ? <button className="mt-2 text-sm font-medium text-rose-700" type="button" onClick={() => removeArrayItem("services", index)}>Remove service</button> : null}
                </div>
              ))}
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => addArrayItem("services", blankService)}>Add service</button>
            </Section>

            <Section id="builder-5" eyebrow="Pets" title="5. Pets and animal transport">
              {form.pets.map((pet, index) => (
                <div className="grid gap-3 rounded-md border border-slate-100 p-3 md:grid-cols-4" key={index}>
                  <Field label="Pet name" value={pet.pet_name} onChange={(value) => updateArray("pets", index, { pet_name: value })} />
                  <Select label="Species" value={pet.species} onChange={(value) => updateArray("pets", index, { species: value })} options={(state?.petSpecies?.length ? state.petSpecies.map((item) => [item.code, item.label]) : [["dog", "Dog"], ["cat", "Cat"]])} />
                  <Field label="Breed" value={pet.breed_free_text || pet.breed} onChange={(value) => updateArray("pets", index, { breed_free_text: value })} />
                  <Select label="Transport" value={pet.requested_transport_mode} onChange={(value) => updateArray("pets", index, { requested_transport_mode: value })} options={[["petc", "PETC cabin"], ["avih", "AVIH hold"], ["manifest_cargo_advisory", "Cargo advisory"]]} />
                  <Field label="Pet kg" type="number" value={pet.pet_weight_kg} onChange={(value) => updateArray("pets", index, { pet_weight_kg: value })} />
                  <Field label="Container kg" type="number" value={pet.container_weight_kg} onChange={(value) => updateArray("pets", index, { container_weight_kg: value })} />
                  <Field label="Combined kg" type="number" value={pet.combined_weight_kg} onChange={(value) => updateArray("pets", index, { combined_weight_kg: value })} />
                  {fieldVisible("pets.documentation_status") ? <Field label="Documents" value={pet.documentation_status} onChange={(value) => updateArray("pets", index, { documentation_status: value })} /> : null}
                  <CheckboxGroup title="Transport segments" values={segmentKeys(form.segments)} selected={pet.segment_keys || []} onToggle={(value) => updateArray("pets", index, { segment_keys: toggleValue(pet.segment_keys || [], value) })} />
                  <TextArea label="Pet requirements" value={pet.notes} onChange={(value) => updateArray("pets", index, { notes: value })} />
                  <button className="text-sm font-medium text-rose-700" type="button" onClick={() => removeArrayItem("pets", index)}>Remove pet</button>
                </div>
              ))}
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => addArrayItem("pets", blankPet)}>Add pet</button>
            </Section>

            <Section id="builder-6" eyebrow="Special items" title="6. Special items and equipment">
              {form.special_items.map((item, index) => (
                <div className="grid gap-3 rounded-md border border-slate-100 p-3 md:grid-cols-4" key={index}>
                  <Select label="Category" value={item.item_category_code} onChange={(value) => updateArray("special_items", index, { item_category_code: value })} options={(state?.specialItemCategories?.length ? state.specialItemCategories.map((entry) => [entry.code, entry.label]) : [["sports_equipment", "Sports equipment"], ["musical_instrument", "Musical instrument"], ["fragile_item", "Fragile item"], ["other", "Other"]])} />
                  <Field label="Item name" value={item.item_name} onChange={(value) => updateArray("special_items", index, { item_name: value })} />
                  <Field label="Description" value={item.description} onChange={(value) => updateArray("special_items", index, { description: value })} required />
                  <Field label="Quantity" type="number" value={item.quantity} onChange={(value) => updateArray("special_items", index, { quantity: value })} />
                  <Field label="Weight kg" type="number" value={item.weight_kg} onChange={(value) => updateArray("special_items", index, { weight_kg: value })} />
                  <Select label="Transport location" value={item.transport_location} onChange={(value) => updateArray("special_items", index, { transport_location: value })} options={[["passenger_cabin", "Passenger cabin"], ["baggage_hold", "Baggage hold"], ["extra_seat", "Extra seat"], ["checked_baggage", "Checked baggage"], ["cargo_advisory", "Cargo advisory"]]} />
                  {fieldVisible("special_items.documentation_status") ? <Field label="Documents" value={item.documentation_status} onChange={(value) => updateArray("special_items", index, { documentation_status: value })} /> : null}
                  <CheckboxGroup title="Transport segments" values={segmentKeys(form.segments)} selected={item.segment_keys || []} onToggle={(value) => updateArray("special_items", index, { segment_keys: toggleValue(item.segment_keys || [], value) })} />
                  <TextArea label="Handling instructions" value={item.notes} onChange={(value) => updateArray("special_items", index, { notes: value })} />
                  <button className="text-sm font-medium text-rose-700" type="button" onClick={() => removeArrayItem("special_items", index)}>Remove item</button>
                </div>
              ))}
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => addArrayItem("special_items", blankSpecialItem)}>Add special item</button>
            </Section>

            <Section id="builder-7" eyebrow="Review" title="7. Notes and summary">
              <div className="grid gap-3 md:grid-cols-3">
                <Select label="Status" value={form.status} onChange={(value) => setField("status", value)} options={["draft", "new", "triage"].map((item) => [item, item])} />
                <Select label="Priority" value={form.priority} onChange={(value) => setField("priority", value)} options={["low", "normal", "high", "urgent"].map((item) => [item, item])} />
                <Select label="Source" value={form.source} onChange={(value) => setField("source", value)} options={["staff_created", "phone", "email", "whatsapp", "walk_in", "public_website", "client_portal", "imported", "internal"].map((item) => [item, item.replaceAll("_", " ")])} />
              </div>
              <Field label="Operational title" value={form.title || derivedTitle} onChange={(value) => setField("title", value)} />
              <TextArea label="Internal notes" value={form.internal_notes} onChange={(value) => setField("internal_notes", value)} />
              <TextArea label="Client-visible notes" value={form.client_visible_notes} onChange={(value) => setField("client_visible_notes", value)} />
              {customFields.length ? (
                <div className="grid gap-3 rounded-md border border-slate-100 p-3 md:grid-cols-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 md:col-span-2">Agency custom fields</p>
                  {customFields.map((field) => <CustomField field={field} value={form.agency_custom_fields[field.field_key] || ""} onChange={(value) => setField("agency_custom_fields", { ...form.agency_custom_fields, [field.field_key]: value })} key={field.field_key} />)}
                </div>
              ) : null}
            </Section>

            <div className="sticky bottom-4 flex justify-end rounded-lg border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur">
              <button className="rounded-md bg-blue-600 px-5 py-3 text-sm font-semibold text-white" type="submit">Create operational request</button>
            </div>
          </form>
          </div>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function serviceDetails(service) {
  if (service.category !== "mobility_assistance") return cleanObject(service.details || {})
  const details = service.details || {}
  const recommendation = recommendMobilitySsr(details)
  const confirmed = details.confirmed_ssr_code === "use_suggested" ? recommendation.code : details.confirmed_ssr_code || recommendation.code
  return cleanObject({
    assessment_version: "v2_assessment_driven",
    passenger_context_tags: details.passenger_context_tags || [],
    passenger_context_notes: details.passenger_context_notes || undefined,
    functional_assessment: cleanObject(details.functional_assessment || {}),
    suggested_ssr_code: recommendation.code,
    suggested_ssr_reason: recommendation.reason,
    recommendation_confidence: recommendation.confidence,
    confirmed_ssr_code: confirmed,
    override_reason: confirmed !== recommendation.code ? details.override_reason : undefined,
    final_assistance_label: details.final_assistance_label || undefined,
    own_mobility_device: details.own_mobility_device || "no",
    own_device_details: (details.own_mobility_device && details.own_mobility_device !== "no") ? cleanObject({ device_type: details.own_mobility_device, ...(details.own_device_details || {}) }) : {},
    battery_details: batteryDeviceTypes.has(details.own_mobility_device) ? cleanObject(details.battery_details || {}) : {},
  })
}

function cleanObject(value) {
  return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== "" && item !== undefined && item !== null))
}

function numericOrUndefined(value) {
  return value === "" || value === undefined || value === null ? undefined : Number(value)
}

function passengerKeys(passengers) {
  return passengers.map((passenger, index) => [`inline-${index}`, passenger.display_name || passenger.first_name || passenger.passenger_id || `Passenger ${index + 1}`])
}

function segmentKeys(segments) {
  return segments.filter((segment) => segment.origin_text && segment.destination_text).map((segment, index) => {
    const key = String(Number(segment.sequence) || index + 1)
    return [key, `${key}. ${segment.origin_text} → ${segment.destination_text}`]
  })
}

function categoryToFamily(category) {
  return {
    mobility_assistance: "wheelchair_mobility",
    medical_travel: "medical_assistance",
    pet_travel: "pets_animals",
    unaccompanied_minor: "minor_assistance",
    child_travel_support: "minor_assistance",
    special_baggage: "special_items",
    sports_equipment: "special_items",
    airport_assistance: "sensory_assistance",
  }[category] || undefined
}

function familyToCategory(family) {
  return {
    wheelchair_mobility: "mobility_assistance",
    medical_assistance: "medical_travel",
    pets_animals: "pet_travel",
    minor_assistance: "unaccompanied_minor",
    special_items: "special_baggage",
    sensory_assistance: "airport_assistance",
  }[family] || undefined
}

function toggleValue(values, value) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value]
}

function recommendMobilitySsr(details = {}) {
  const tags = details.passenger_context_tags || []
  const assessment = details.functional_assessment || {}
  const wheelchairRequired = assessment.needs_wheelchair_for_distance === "yes" || assessment.needs_wheelchair_to_aircraft_door === "yes"
  const noWheelchair = assessment.needs_wheelchair_for_distance === "no" && assessment.needs_wheelchair_to_aircraft_door === "no" && assessment.needs_assistance_into_aircraft_seat !== "yes" && assessment.needs_aisle_chair !== "yes"
  if (assessment.needs_assistance_into_aircraft_seat === "yes" || assessment.needs_aisle_chair === "yes" || assessment.can_transfer_independently_to_aircraft_seat === "no" || assessment.can_walk_short_distances === "no") {
    return { code: "WCHC", confidence: "high", reason: "Passenger cannot walk/self-transfer fully or needs aisle chair / seat assistance." }
  }
  if (assessment.can_climb_aircraft_stairs === "no" || assessment.can_board_without_lift_or_stair_assistance === "no" || assessment.needs_wheelchair_to_aircraft_door === "yes") {
    return { code: "WCHS", confidence: "high", reason: "Passenger can manage short distance but cannot use stairs or needs assistance to aircraft door." }
  }
  if (wheelchairRequired && assessment.can_walk_short_distances === "yes" && assessment.can_climb_aircraft_stairs === "yes") {
    return { code: "WCHR", confidence: "high", reason: "Passenger can walk/use stairs but needs wheelchair for airport distance." }
  }
  if (tags.includes("medical_condition") || assessment.medical_clearance_needed === "yes" || assessment.oxygen_needed === "yes" || assessment.stretcher_needed === "yes") {
    return { code: "MEDA", confidence: "medium", reason: "Medical context or medical assistance indicators require staff review for MEDA handling." }
  }
  if (tags.includes("blind_visual_impairment") && noWheelchair) {
    return { code: "BLND", confidence: "medium", reason: "Visual impairment selected and no wheelchair need indicated." }
  }
  if (tags.includes("deaf_hard_of_hearing") && noWheelchair) {
    return { code: "DEAF", confidence: "medium", reason: "Hearing impairment selected and no wheelchair need indicated." }
  }
  if (assessment.needs_escort_meet_and_assist_only === "yes" && noWheelchair) {
    return { code: "MAAS", confidence: "medium", reason: "Passenger needs navigation/escort support only; wheelchair is not indicated." }
  }
  return { code: "manual_review", confidence: "manual_review", reason: "Information is insufficient or conflicting; staff should assess manually." }
}

function Section({ id, eyebrow, title, children }) {
  return (
    <section id={id} className="scroll-mt-24 space-y-4 rounded-lg border border-slate-200 bg-white p-5">
      <div className="border-b border-slate-100 pb-3">
        {eyebrow ? <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{eyebrow}</p> : null}
        <h3 className="mt-1 font-semibold text-slate-950">{title}</h3>
      </div>
      {children}
    </section>
  )
}

function Field({ label, value, onChange, type = "text", required = false }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value} required={required} onChange={(event) => onChange(event.target.value)} /></label>
}

function CustomField({ field, value, onChange }) {
  const label = field.effective_label || field.label || field.field_key
  if (field.field_type === "textarea") {
    return <TextArea label={label} value={value} onChange={onChange} />
  }
  if (field.field_type === "boolean") {
    return <label className="flex items-center gap-2 rounded-md bg-slate-50 p-3 text-sm text-slate-700"><input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} /> {label}</label>
  }
  const type = field.field_type === "number" ? "number" : field.field_type === "date" ? "date" : "text"
  return <Field label={label} type={type} value={value} required={field.required} onChange={onChange} />
}

function TextArea({ label, value, onChange }) {
  return <label className="block text-sm font-medium text-slate-700 md:col-span-2">{label}<textarea className="mt-2 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, onChange, options, required = false }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} required={required} onChange={(event) => onChange(event.target.value)}>{options.map(([optionValue, labelText]) => <option key={optionValue} value={optionValue}>{labelText}</option>)}</select></label>
}

function CheckboxGroup({ title, values, selected, onToggle }) {
  return (
    <div className="mt-3 rounded-md border border-slate-100 p-3 md:col-span-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <div className="mt-2 flex flex-wrap gap-3">
        {values.map(([value, label]) => (
          <label className="flex items-center gap-2 text-sm text-slate-700" key={value}>
            <input type="checkbox" checked={(selected || []).includes(value)} onChange={() => onToggle(value)} />
            {label}
          </label>
        ))}
      </div>
      {!values.length ? <p className="mt-2 text-xs text-amber-700">Add itinerary segments first.</p> : null}
    </div>
  )
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
    const assessment = details.functional_assessment || {}
    const ownDevice = details.own_mobility_device || "no"
    const ownDeviceDetails = details.own_device_details || {}
    const batteryDetails = details.battery_details || {}
    const recommendation = recommendMobilitySsr(details)
    const confirmed = details.confirmed_ssr_code || "use_suggested"
    const finalCode = confirmed === "use_suggested" ? recommendation.code : confirmed
    const overrideRequired = confirmed !== "use_suggested" && finalCode !== recommendation.code
    const showDeviceDetails = ownDevice && ownDevice !== "no"
    const showBatteryDetails = batteryDeviceTypes.has(ownDevice)
    return (
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <ServiceCard title="Passenger context" body="Capture why assistance may be needed. Do not include sensitive medical detail unless operationally required.">
          <p className="rounded-md bg-amber-50 p-3 text-xs leading-5 text-amber-900">V1 applies mobility services to all selected passengers by default. Per-passenger assignment is planned for a later editing pass.</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {contextTagOptions.map(([value, label]) => (
              <label className="flex items-center gap-2 text-sm text-slate-700" key={value}>
                <input type="checkbox" checked={(details.passenger_context_tags || []).includes(value)} onChange={() => onChange({ passenger_context_tags: toggleValue(details.passenger_context_tags || [], value) })} />
                {label}
              </label>
            ))}
          </div>
          <TextArea label="Reason / diagnosis / operational context" value={details.passenger_context_notes || ""} onChange={(value) => onChange({ passenger_context_notes: value })} />
        </ServiceCard>
        <ServiceCard title="Functional assessment" body="Answer the operational capability questions first. SSR/service code is suggested from these answers.">
          <div className="grid gap-3 md:grid-cols-2">
            <Select label="Can walk through terminal without wheelchair?" value={assessment.can_walk_terminal_without_wheelchair || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, can_walk_terminal_without_wheelchair: value } })} options={triStateOptions} />
            <Select label="Can walk short distances?" value={assessment.can_walk_short_distances || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, can_walk_short_distances: value } })} options={triStateOptions} />
            <Select label="Can climb aircraft stairs?" value={assessment.can_climb_aircraft_stairs || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, can_climb_aircraft_stairs: value } })} options={triStateOptions} />
            <Select label="Can board without lift/stair assistance?" value={assessment.can_board_without_lift_or_stair_assistance || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, can_board_without_lift_or_stair_assistance: value } })} options={triStateOptions} />
            <Select label="Can transfer independently to aircraft seat?" value={assessment.can_transfer_independently_to_aircraft_seat || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, can_transfer_independently_to_aircraft_seat: value } })} options={triStateOptions} />
            <Select label="Needs wheelchair for airport distance?" value={assessment.needs_wheelchair_for_distance || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, needs_wheelchair_for_distance: value } })} options={triStateOptions} />
            <Select label="Needs wheelchair to/from aircraft door?" value={assessment.needs_wheelchair_to_aircraft_door || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, needs_wheelchair_to_aircraft_door: value } })} options={triStateOptions} />
            <Select label="Needs assistance into aircraft seat?" value={assessment.needs_assistance_into_aircraft_seat || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, needs_assistance_into_aircraft_seat: value } })} options={triStateOptions} />
            <Select label="Needs aisle chair?" value={assessment.needs_aisle_chair || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, needs_aisle_chair: value } })} options={triStateOptions} />
            <Select label="Needs escort / meet-and-assist only?" value={assessment.needs_escort_meet_and_assist_only || "unknown"} onChange={(value) => onChange({ functional_assessment: { ...assessment, needs_escort_meet_and_assist_only: value } })} options={triStateOptions} />
          </div>
        </ServiceCard>
        <ServiceCard title="Suggested SSR / service code" body="Derived from assessment answers. This does not transmit anything to an airline.">
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Suggested code</p>
            <p className="mt-1 text-2xl font-semibold text-blue-950">{recommendation.code}</p>
            <p className="mt-2 text-sm leading-6 text-blue-900">{recommendation.reason}</p>
            <p className="mt-2 text-xs font-medium text-blue-800">Confidence: {recommendation.confidence.replaceAll("_", " ")}</p>
          </div>
        </ServiceCard>
        <ServiceCard title="Staff confirmation" body="Use the suggestion or override it. Overrides should include an operational reason.">
          <Select label="Confirmed SSR/service code" value={confirmed} onChange={(value) => onChange({ confirmed_ssr_code: value })} options={ssrCodeOptions} />
          {overrideRequired ? <Field label="Override reason" value={details.override_reason || ""} onChange={(value) => onChange({ override_reason: value })} required /> : null}
          <Field label="Final assistance label / operational notes" value={details.final_assistance_label || ""} onChange={(value) => onChange({ final_assistance_label: value })} />
        </ServiceCard>
        <ServiceCard title="Own mobility device" body="Supplemental device details; this is separate from the assistance SSR recommendation.">
          <Select label="Travelling with own wheelchair or mobility device?" value={ownDevice} onChange={(value) => onChange({ own_mobility_device: value, own_device_details: value === "no" ? {} : { ...ownDeviceDetails, device_type: value }, battery_details: batteryDeviceTypes.has(value) ? batteryDetails : {} })} options={ownMobilityDeviceOptions} />
          {showDeviceDetails ? (
            <div className="mt-3 grid gap-3">
              <Field label="Brand / model" value={ownDeviceDetails.brand_model || ""} onChange={(value) => onChange({ own_device_details: { ...ownDeviceDetails, brand_model: value } })} />
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Weight kg" type="number" value={ownDeviceDetails.weight_kg || ""} onChange={(value) => onChange({ own_device_details: { ...ownDeviceDetails, weight_kg: value } })} />
                <Select label="Foldable / collapsible" value={ownDeviceDetails.foldable_or_collapsible || "unknown"} onChange={(value) => onChange({ own_device_details: { ...ownDeviceDetails, foldable_or_collapsible: value } })} options={triStateOptions} />
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <Field label="Length cm" type="number" value={ownDeviceDetails.length_cm || ""} onChange={(value) => onChange({ own_device_details: { ...ownDeviceDetails, length_cm: value } })} />
                <Field label="Width cm" type="number" value={ownDeviceDetails.width_cm || ""} onChange={(value) => onChange({ own_device_details: { ...ownDeviceDetails, width_cm: value } })} />
                <Field label="Height cm" type="number" value={ownDeviceDetails.height_cm || ""} onChange={(value) => onChange({ own_device_details: { ...ownDeviceDetails, height_cm: value } })} />
              </div>
              <Field label="Device notes" value={ownDeviceDetails.notes || ""} onChange={(value) => onChange({ own_device_details: { ...ownDeviceDetails, notes: value } })} />
            </div>
          ) : null}
          {showBatteryDetails ? (
            <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3">
              <p className="text-sm font-semibold text-amber-950">Battery details</p>
              <div className="mt-3 grid gap-3">
                <Select label="Battery type" value={batteryDetails.battery_type || "unknown"} onChange={(value) => onChange({ battery_details: { ...batteryDetails, battery_type: value } })} options={[["dry_gel_sealed_lead_acid", "Dry / gel / sealed lead acid"], ["lithium_ion", "Lithium ion"], ["spillable_wet_cell", "Spillable wet cell"], ["unknown", "Unknown"]]} />
                <Select label="Battery removable?" value={batteryDetails.battery_removable || "unknown"} onChange={(value) => onChange({ battery_details: { ...batteryDetails, battery_removable: value } })} options={triStateOptions} />
                <div className="grid gap-3 sm:grid-cols-3">
                  <Field label="Watt hours" type="number" value={batteryDetails.battery_watt_hours || ""} onChange={(value) => onChange({ battery_details: { ...batteryDetails, battery_watt_hours: value } })} />
                  <Field label="Voltage" type="number" value={batteryDetails.battery_voltage || ""} onChange={(value) => onChange({ battery_details: { ...batteryDetails, battery_voltage: value } })} />
                  <Field label="Amp hours" type="number" value={batteryDetails.battery_amp_hours || ""} onChange={(value) => onChange({ battery_details: { ...batteryDetails, battery_amp_hours: value } })} />
                </div>
                <Select label="Spare battery carried?" value={batteryDetails.spare_battery_carried || "unknown"} onChange={(value) => onChange({ battery_details: { ...batteryDetails, spare_battery_carried: value } })} options={triStateOptions} />
                <Select label="Battery documentation available?" value={batteryDetails.battery_documentation_available || "unknown"} onChange={(value) => onChange({ battery_details: { ...batteryDetails, battery_documentation_available: value } })} options={triStateOptions} />
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
