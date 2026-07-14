import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "ready_to_book", "booking_in_progress", "booked", "blocked", "cancelled"]
const providers = ["manual", "travelport", "amadeus", "ndc", "supplier", "other"]
const passengerTypes = ["adult", "child", "infant", "other"]
const serviceCategories = ["mobility assistance", "medical", "pet in cabin", "animal in hold", "special baggage", "meet and assist", "child assistance", "VIP handling"]

const emptyPassenger = {
  passenger_type: "adult",
  title: "",
  first_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "",
  nationality: "",
  passenger_id: "",
  notes: "",
}

const emptySegment = {
  segment_number: "1",
  marketing_airline: "",
  operating_airline: "",
  flight_number: "",
  departure_airport: "",
  arrival_airport: "",
  departure_date: "",
  departure_time: "",
  arrival_date: "",
  arrival_time: "",
  cabin: "",
  booking_class: "",
  status_code: "HK",
  aircraft: "",
  notes: "",
}

const emptyPricing = {
  currency: "EUR",
  base_fare: "",
  taxes: "",
  fees: "",
  total: "",
  fare_basis: "",
  tour_code: "",
  pricing_notes: "",
}

const emptySsr = {
  ssr_code: "",
  airline: "",
  passenger_reference: "",
  segment_reference: "",
  free_text: "",
  status: "",
}

const emptyOsi = {
  airline: "",
  text: "",
  passenger_reference: "",
}

const emptyService = {
  service_category: "",
  service_label: "",
  passenger_reference: "",
  segment_reference: "",
  quantity: "1",
  notes: "",
  service_catalogue_id: "",
}

function defaultManualForm(prefilledTripId = "") {
  return {
    title: "",
    trip_id: prefilledTripId,
    client_id: "",
    pnr_locator: "",
    provider_target: "manual",
    internal_notes: "",
    passengers: [{ ...emptyPassenger }],
    segments: [{ ...emptySegment }],
    pricing: { ...emptyPricing },
    ssr: [],
    osi: [],
    services: [],
    raw_overrides: {
      passengers_json: "",
      segments_json: "",
      pricing_json: "",
      ssr_json: "",
      osi_json: "",
      services_json: "",
    },
  }
}

function initialManualForm() {
  const params = new URLSearchParams(window.location.search)
  return defaultManualForm(params.get("trip_id") || "")
}

export default function BookingWorkspacesPage() {
  const initialMode = new URLSearchParams(window.location.search).get("mode") === "manual_booking" ? "manual" : "readiness"
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ status: "", provider_target: "", search: "" })
  const [createModalOpen, setCreateModalOpen] = useState(initialMode === "manual")
  const [createMode, setCreateMode] = useState(initialMode)
  const [selectedPackageId, setSelectedPackageId] = useState("")
  const [manualForm, setManualForm] = useState(initialManualForm)
  const [readinessLoading, setReadinessLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState("")
  const [createError, setCreateError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const query = new URLSearchParams()
    if (filters.status) query.set("status", filters.status)
    if (filters.provider_target) query.set("provider_target", filters.provider_target)
    const suffix = query.toString() ? `?${query.toString()}` : ""
    const [workspaces, readinessPackages] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/booking-workspaces${suffix}`),
      apiGet(`/api/agencies/${context.agency.id}/booking-readiness-packages`),
    ])
    const packages = readinessPackages.items || []
    setState({ ...context, workspaces: workspaces.items || [], readinessPackages: packages })
    setSelectedPackageId((current) => current && packages.some((item) => item.id === current) ? current : packages[0]?.id || "")
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [filters.status, filters.provider_target])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.workspaces || []).filter((workspace) => {
      const record = workspace.booking_record || {}
      const trip = workspace.trip_summary || {}
      return !search || [
        workspace.workspace_number,
        workspace.title,
        trip.trip_reference,
        trip.trip_title,
        record.pnr_locator,
        workspace.request_id,
      ].some((value) => String(value || "").toLowerCase().includes(search))
    })
  }, [filters.search, state])

  const selectedPackage = useMemo(
    () => (state?.readinessPackages || []).find((item) => item.id === selectedPackageId),
    [selectedPackageId, state],
  )

  async function refreshReadinessPackages() {
    const agencyId = state?.agency?.id
    if (!agencyId) return
    setReadinessLoading(true)
    setCreateError("")
    try {
      const readinessPackages = await apiGet(`/api/agencies/${agencyId}/booking-readiness-packages`)
      const packages = readinessPackages.items || []
      setState((current) => current ? { ...current, readinessPackages: packages } : current)
      setSelectedPackageId((current) => current && packages.some((item) => item.id === current) ? current : packages[0]?.id || "")
    } catch (err) {
      setCreateError(err.message)
    } finally {
      setReadinessLoading(false)
    }
  }

  function openCreateModal() {
    setCreateModalOpen(true)
    setCreateMode("readiness")
    setCreateError("")
    refreshReadinessPackages()
  }

  async function createOrOpenBookingWorkspace() {
    if (!selectedPackage) {
      setCreateError("Select a booking readiness package first.")
      return
    }
    if (selectedPackage.booking_workspace_already_exists && selectedPackage.booking_workspace_id) {
      window.location.href = `/agency/booking-workspaces/${selectedPackage.booking_workspace_id}`
      return
    }
    setCreating(true)
    setCreateError("")
    try {
      const payload = {
        booking_readiness_package_id: selectedPackage.id,
        create_draft_record: true,
        ...(selectedPackage.provider_target ? { provider_target: selectedPackage.provider_target } : {}),
      }
      const created = await apiPost(`/api/agencies/${state.agency.id}/booking-workspaces/from-readiness`, payload)
      window.location.href = `/agency/booking-workspaces/${created.booking_workspace.id}`
    } catch (err) {
      setCreateError(err.message)
      setCreating(false)
    }
  }

  async function createManualBookingWorkspace() {
    setCreating(true)
    setCreateError("")
    try {
      const payload = buildManualBookingPayload(manualForm)
      const created = await apiPost(`/api/agencies/${state.agency.id}/booking-workspaces/manual`, payload)
      window.location.href = `/agency/booking-workspaces/${created.booking_workspace.id}`
    } catch (err) {
      setCreateError(err.message)
      setCreating(false)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="text-2xl font-semibold text-slate-950">Booking Workspaces</h2>
              <p className="mt-1 text-sm text-slate-600">PNR mirrors from accepted offers, manual entry, imports, and existing-trip changes.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={openCreateModal}>Create booking workspace</button>
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/bookings">Legacy bookings</a>
            </div>
          </div>

          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-3">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search workspace, trip, PNR" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {statuses.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.provider_target} onChange={(event) => setFilters({ ...filters, provider_target: event.target.value })}>
              <option value="">All providers</option>
              {providers.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
          </section>

          {filtered.length ? (
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <div className="grid grid-cols-[1.2fr_1.3fr_0.9fr_0.9fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <span>Workspace</span>
                <span>Trip / request</span>
                <span>Provider</span>
                <span>Status</span>
                <span>Booking</span>
                <span>Warnings</span>
                <span>Created</span>
              </div>
              <div className="divide-y divide-slate-100">
                {filtered.map((workspace) => (
                  <a className="grid grid-cols-[1.2fr_1.3fr_0.9fr_0.9fr_0.8fr_0.8fr_0.8fr] gap-3 px-4 py-4 text-sm text-slate-700 hover:bg-blue-50/60" href={`/agency/booking-workspaces/${workspace.id}`} key={workspace.id}>
                    <span>
                      <span className="block font-semibold text-slate-950">{workspace.workspace_number}</span>
                      <span className="block truncate text-xs text-slate-500">{workspace.title}</span>
                    </span>
                    <span>
                      <span className="block font-medium text-slate-900">{workspace.trip_summary?.trip_reference || workspace.trip_id}</span>
                      <span className="block truncate text-xs text-slate-500">{workspace.request_id || "No request link"}</span>
                    </span>
                    <span>{label(workspace.provider_target)}</span>
                    <span>{label(workspace.status)}</span>
                    <span>
                      <span className="block">{label(workspace.booking_record?.booking_status || "draft")}</span>
                      <span className="block text-xs text-slate-500">{workspace.booking_record?.pnr_locator || "PNR pending"}</span>
                    </span>
                    <span>{workspace.warning_count || 0}</span>
                    <span>{dateLabel(workspace.created_at)}</span>
                  </a>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState title="No booking workspaces found" body="Create a booking workspace from an accepted offer readiness package, manual entry, or an import draft.">
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={openCreateModal}>Create booking workspace</button>
            </EmptyState>
          )}

          {createModalOpen ? (
            <CreateBookingWorkspaceModal
              creating={creating}
              error={createError}
              loading={readinessLoading}
              onClose={() => setCreateModalOpen(false)}
              mode={createMode}
              manualForm={manualForm}
              onManualChange={(updates) => setManualForm((current) => ({ ...current, ...updates }))}
              onManualSubmit={createManualBookingWorkspace}
              onModeChange={setCreateMode}
              onSelect={setSelectedPackageId}
              onSubmit={createOrOpenBookingWorkspace}
              packages={state?.readinessPackages || []}
              selectedPackage={selectedPackage}
              selectedPackageId={selectedPackageId}
            />
          ) : null}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function CreateBookingWorkspaceModal({ creating, error, loading, manualForm, mode, onClose, onManualChange, onManualSubmit, onModeChange, onSelect, onSubmit, packages, selectedPackage, selectedPackageId }) {
  const actionLabel = selectedPackage?.booking_workspace_already_exists ? "Open booking workspace" : "Create booking workspace"
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <section className="flex max-h-[90vh] w-full max-w-6xl flex-col overflow-hidden rounded-lg bg-white shadow-xl">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 p-5">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Booking workspace</p>
            <h3 className="text-xl font-semibold text-slate-950">Create booking workspace</h3>
            <p className="mt-1 text-sm text-slate-600">Create an internal mirror only. No live booking or provider action will run.</p>
            {selectedPackage ? (
              <a className="mt-2 inline-flex rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/booking-handoffs?acceptance_id=${selectedPackage.acceptance_id || ""}&booking_readiness_package_id=${selectedPackage.id}&trip_id=${selectedPackage.trip_id || ""}`}>
                Review booking handoff first
              </a>
            ) : null}
          </div>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onClose}>Close</button>
        </div>
        <div className="overflow-y-auto p-5">
          {error ? <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          <div className="mb-4 grid gap-2 md:grid-cols-3">
            <ModeButton active={mode === "readiness"} label="From accepted offer readiness package" onClick={() => onModeChange("readiness")} />
            <ModeButton active={mode === "manual"} label="Manual booking" onClick={() => onModeChange("manual")} />
            <ModeButton active={mode === "import"} label="Import from GDS / confirmation text" onClick={() => onModeChange("import")} />
          </div>

          {mode === "readiness" && loading ? <p className="text-sm text-slate-600">Loading booking readiness packages...</p> : null}
          {mode === "readiness" && !loading && packages.length ? (
            <div className="space-y-3">
              {packages.map((item) => (
                <button
                  className={`w-full rounded-lg border p-4 text-left transition ${selectedPackageId === item.id ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white hover:border-blue-300"}`}
                  key={item.id}
                  onClick={() => onSelect(item.id)}
                  type="button"
                >
                  <div className="grid gap-3 lg:grid-cols-[1.2fr_1.2fr_0.8fr_0.8fr_0.7fr_0.8fr]">
                    <SummaryBlock label="Trip" value={tripLabel(item)} subvalue={item.trip_summary?.trip_title || item.trip_id || "No trip summary"} />
                    <SummaryBlock label="Accepted offer / workspace" value={offerLabel(item)} subvalue={item.accepted_offer_summary?.id || item.acceptance_id || "No acceptance summary"} />
                    <SummaryBlock label="Provider" value={label(item.provider_target || "manual")} />
                    <SummaryBlock label="Status" value={label(item.status)} />
                    <SummaryBlock label="Warnings" value={String(item.warning_count || 0)} subvalue={`${item.policy_violation_count || 0} policy`} />
                    <SummaryBlock label="Created" value={dateLabel(item.created_at)} />
                  </div>
                  {item.booking_workspace_already_exists ? (
                    <div className="mt-3 rounded-md bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800">
                      Booking workspace already exists: {item.booking_workspace_summary?.workspace_number || item.booking_workspace_id}
                    </div>
                  ) : null}
                </button>
              ))}
            </div>
          ) : null}
          {mode === "readiness" && !loading && !packages.length ? (
            <EmptyState title="No booking readiness packages found" body="Accept an offer option first so AgencyOS can create a booking readiness package." />
          ) : null}
          {mode === "manual" ? (
            <ManualBookingForm form={manualForm} onChange={onManualChange} />
          ) : null}
          {mode === "import" ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm font-semibold text-slate-950">Import from GDS / confirmation text</p>
              <p className="mt-1 text-sm text-slate-600">Create an import draft, parse a conservative preview, then import it into internal booking/ticket/EMD mirrors only.</p>
              <a className="mt-4 inline-flex rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold" href="/agency/booking-imports">Open booking imports</a>
            </div>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 p-5">
          <p className="text-sm text-slate-600">{mode === "readiness" ? (selectedPackage ? selectedPackage.id : "No package selected") : "Provider execution disabled"}</p>
          {mode === "readiness" ? (
            <button className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={onSubmit} disabled={!selectedPackage || creating}>
              {creating ? "Working..." : actionLabel}
            </button>
          ) : null}
          {mode === "manual" ? (
            <button className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={onManualSubmit} disabled={creating}>
              {creating ? "Working..." : "Create manual booking"}
            </button>
          ) : null}
        </div>
      </section>
    </div>
  )
}

function ManualBookingForm({ form, onChange }) {
  function updateList(name, index, updates) {
    onChange({ [name]: form[name].map((item, itemIndex) => itemIndex === index ? { ...item, ...updates } : item) })
  }

  function addListItem(name, template) {
    const next = { ...template }
    if (name === "segments") next.segment_number = String(form.segments.length + 1)
    onChange({ [name]: [...form[name], next] })
  }

  function removeListItem(name, index) {
    onChange({ [name]: form[name].filter((_, itemIndex) => itemIndex !== index) })
  }

  return (
    <div className="space-y-5">
      <FormSection title="Booking basics">
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          <Field label="Title" value={form.title} onChange={(value) => onChange({ title: value })} />
          <Field label="Existing trip id/reference" value={form.trip_id} onChange={(value) => onChange({ trip_id: value })} />
          <Field label="Client id" value={form.client_id} onChange={(value) => onChange({ client_id: value })} />
          <Field label="PNR locator" value={form.pnr_locator} onChange={(value) => onChange({ pnr_locator: value.toUpperCase() })} />
          <label className="text-sm font-medium text-slate-700">
            Provider target
            <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.provider_target} onChange={(event) => onChange({ provider_target: event.target.value })}>
              {providers.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
          </label>
          <TextArea label="Internal notes" value={form.internal_notes} onChange={(value) => onChange({ internal_notes: value })} plain />
        </div>
      </FormSection>

      <FormSection title="Passengers">
        <RepeatableHeader label="Passenger" onAdd={() => addListItem("passengers", emptyPassenger)} />
        <div className="space-y-3">
          {form.passengers.map((passenger, index) => (
            <div className="rounded-lg border border-slate-200 p-3" key={`passenger-${index}`}>
              <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-4">
                <SelectField label="Passenger type" value={passenger.passenger_type} options={passengerTypes} onChange={(value) => updateList("passengers", index, { passenger_type: value })} />
                <Field label="Title" value={passenger.title} onChange={(value) => updateList("passengers", index, { title: value })} />
                <Field label="First name" value={passenger.first_name} onChange={(value) => updateList("passengers", index, { first_name: value })} />
                <Field label="Last name" value={passenger.last_name} onChange={(value) => updateList("passengers", index, { last_name: value })} />
                <Field label="Date of birth" type="date" value={passenger.date_of_birth} onChange={(value) => updateList("passengers", index, { date_of_birth: value })} />
                <Field label="Gender optional" value={passenger.gender} onChange={(value) => updateList("passengers", index, { gender: value })} />
                <Field label="Nationality optional" value={passenger.nationality} onChange={(value) => updateList("passengers", index, { nationality: value.toUpperCase() })} />
                <Field label="Passenger id optional" value={passenger.passenger_id} onChange={(value) => updateList("passengers", index, { passenger_id: value })} />
                <Field label="Notes optional" value={passenger.notes} onChange={(value) => updateList("passengers", index, { notes: value })} />
              </div>
              <RemoveButton disabled={form.passengers.length === 1} label="Remove passenger" onClick={() => removeListItem("passengers", index)} />
            </div>
          ))}
        </div>
      </FormSection>

      <FormSection title="Flight segments">
        <RepeatableHeader label="Flight segment" onAdd={() => addListItem("segments", emptySegment)} />
        <div className="space-y-3">
          {form.segments.map((segment, index) => (
            <div className="rounded-lg border border-slate-200 p-3" key={`segment-${index}`}>
              <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-4">
                <Field label="Segment number" value={segment.segment_number} onChange={(value) => updateList("segments", index, { segment_number: value })} />
                <Field label="Marketing airline" value={segment.marketing_airline} onChange={(value) => updateList("segments", index, { marketing_airline: value.toUpperCase() })} />
                <Field label="Operating airline" value={segment.operating_airline} onChange={(value) => updateList("segments", index, { operating_airline: value.toUpperCase() })} />
                <Field label="Flight number" value={segment.flight_number} onChange={(value) => updateList("segments", index, { flight_number: value })} />
                <Field label="Departure airport" value={segment.departure_airport} onChange={(value) => updateList("segments", index, { departure_airport: value.toUpperCase() })} />
                <Field label="Arrival airport" value={segment.arrival_airport} onChange={(value) => updateList("segments", index, { arrival_airport: value.toUpperCase() })} />
                <Field label="Departure date" type="date" value={segment.departure_date} onChange={(value) => updateList("segments", index, { departure_date: value })} />
                <Field label="Departure time" type="time" value={segment.departure_time} onChange={(value) => updateList("segments", index, { departure_time: value })} />
                <Field label="Arrival date" type="date" value={segment.arrival_date} onChange={(value) => updateList("segments", index, { arrival_date: value })} />
                <Field label="Arrival time" type="time" value={segment.arrival_time} onChange={(value) => updateList("segments", index, { arrival_time: value })} />
                <Field label="Cabin" value={segment.cabin} onChange={(value) => updateList("segments", index, { cabin: value })} />
                <Field label="Booking class / RBD" value={segment.booking_class} onChange={(value) => updateList("segments", index, { booking_class: value.toUpperCase() })} />
                <Field label="Status code" value={segment.status_code} onChange={(value) => updateList("segments", index, { status_code: value.toUpperCase() })} />
                <Field label="Aircraft optional" value={segment.aircraft} onChange={(value) => updateList("segments", index, { aircraft: value })} />
                <Field label="Notes optional" value={segment.notes} onChange={(value) => updateList("segments", index, { notes: value })} />
              </div>
              <RemoveButton disabled={form.segments.length === 1} label="Remove segment" onClick={() => removeListItem("segments", index)} />
            </div>
          ))}
        </div>
      </FormSection>

      <FormSection title="Pricing">
        <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-4">
          <Field label="Currency" value={form.pricing.currency} onChange={(value) => onChange({ pricing: { ...form.pricing, currency: value.toUpperCase() } })} />
          <Field label="Base fare" type="number" value={form.pricing.base_fare} onChange={(value) => onChange({ pricing: { ...form.pricing, base_fare: value } })} />
          <Field label="Taxes" type="number" value={form.pricing.taxes} onChange={(value) => onChange({ pricing: { ...form.pricing, taxes: value } })} />
          <Field label="Fees" type="number" value={form.pricing.fees} onChange={(value) => onChange({ pricing: { ...form.pricing, fees: value } })} />
          <Field label="Total" type="number" value={form.pricing.total} onChange={(value) => onChange({ pricing: { ...form.pricing, total: value } })} />
          <Field label="Fare basis optional" value={form.pricing.fare_basis} onChange={(value) => onChange({ pricing: { ...form.pricing, fare_basis: value.toUpperCase() } })} />
          <Field label="Tour code / account code optional" value={form.pricing.tour_code} onChange={(value) => onChange({ pricing: { ...form.pricing, tour_code: value } })} />
          <Field label="Pricing notes optional" value={form.pricing.pricing_notes} onChange={(value) => onChange({ pricing: { ...form.pricing, pricing_notes: value } })} />
        </div>
      </FormSection>

      <FormSection title="SSR entries">
        <RepeatableHeader label="SSR" onAdd={() => addListItem("ssr", emptySsr)} />
        <ExampleText text="Examples: WCHR, PETC, AVIH, MAAS, MEDA, XBAG" />
        <div className="space-y-3">
          {form.ssr.map((item, index) => (
            <div className="rounded-lg border border-slate-200 p-3" key={`ssr-${index}`}>
              <div className="grid gap-3 md:grid-cols-3">
                <Field label="SSR code" value={item.ssr_code} onChange={(value) => updateList("ssr", index, { ssr_code: value.toUpperCase() })} />
                <Field label="Airline optional" value={item.airline} onChange={(value) => updateList("ssr", index, { airline: value.toUpperCase() })} />
                <Field label="Passenger reference optional" value={item.passenger_reference} onChange={(value) => updateList("ssr", index, { passenger_reference: value })} />
                <Field label="Segment reference optional" value={item.segment_reference} onChange={(value) => updateList("ssr", index, { segment_reference: value })} />
                <Field label="Free text" value={item.free_text} onChange={(value) => updateList("ssr", index, { free_text: value })} />
                <Field label="Status optional" value={item.status} onChange={(value) => updateList("ssr", index, { status: value.toUpperCase() })} />
              </div>
              <RemoveButton label="Remove SSR" onClick={() => removeListItem("ssr", index)} />
            </div>
          ))}
        </div>
      </FormSection>

      <FormSection title="OSI entries">
        <RepeatableHeader label="OSI" onAdd={() => addListItem("osi", emptyOsi)} />
        <div className="space-y-3">
          {form.osi.map((item, index) => (
            <div className="rounded-lg border border-slate-200 p-3" key={`osi-${index}`}>
              <div className="grid gap-3 md:grid-cols-3">
                <Field label="Airline optional" value={item.airline} onChange={(value) => updateList("osi", index, { airline: value.toUpperCase() })} />
                <Field label="Text" value={item.text} onChange={(value) => updateList("osi", index, { text: value })} />
                <Field label="Passenger reference optional" value={item.passenger_reference} onChange={(value) => updateList("osi", index, { passenger_reference: value })} />
              </div>
              <RemoveButton label="Remove OSI" onClick={() => removeListItem("osi", index)} />
            </div>
          ))}
        </div>
      </FormSection>

      <FormSection title="Services / special handling">
        <RepeatableHeader label="Service" onAdd={() => addListItem("services", emptyService)} />
        <ExampleText text={`Examples: ${serviceCategories.join(", ")}`} />
        <div className="space-y-3">
          {form.services.map((item, index) => (
            <div className="rounded-lg border border-slate-200 p-3" key={`service-${index}`}>
              <div className="grid gap-3 md:grid-cols-3">
                <Field label="Service category" value={item.service_category} onChange={(value) => updateList("services", index, { service_category: value })} />
                <Field label="Service label" value={item.service_label} onChange={(value) => updateList("services", index, { service_label: value })} />
                <Field label="Passenger reference optional" value={item.passenger_reference} onChange={(value) => updateList("services", index, { passenger_reference: value })} />
                <Field label="Segment reference optional" value={item.segment_reference} onChange={(value) => updateList("services", index, { segment_reference: value })} />
                <Field label="Quantity" type="number" value={item.quantity} onChange={(value) => updateList("services", index, { quantity: value })} />
                <Field label="Notes" value={item.notes} onChange={(value) => updateList("services", index, { notes: value })} />
                <Field label="Service catalogue id optional" value={item.service_catalogue_id} onChange={(value) => updateList("services", index, { service_catalogue_id: value })} />
              </div>
              <RemoveButton label="Remove service" onClick={() => removeListItem("services", index)} />
            </div>
          ))}
        </div>
      </FormSection>

      <details className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced raw snapshots</summary>
        <p className="mt-2 text-sm text-slate-600">Advanced only. Structured fields above are used unless a raw override is provided.</p>
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          {Object.entries(form.raw_overrides).map(([key, value]) => (
            <TextArea
              key={key}
              label={`${key} override`}
              value={value}
              onChange={(next) => onChange({ raw_overrides: { ...form.raw_overrides, [key]: next } })}
            />
          ))}
        </div>
      </details>
    </div>
  )
}

function FormSection({ title, children }) {
  return (
    <section className="space-y-3 border-t border-slate-200 pt-4 first:border-t-0 first:pt-0">
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      {children}
    </section>
  )
}

function RepeatableHeader({ label: itemLabel, onAdd }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <p className="text-sm text-slate-600">{itemLabel} rows</p>
      <button className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-semibold" type="button" onClick={onAdd}>Add {itemLabel.toLowerCase()}</button>
    </div>
  )
}

function RemoveButton({ disabled, label: buttonLabel, onClick }) {
  return (
    <button className="mt-3 rounded-md border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-600 disabled:opacity-50" type="button" onClick={onClick} disabled={disabled}>
      {buttonLabel}
    </button>
  )
}

function ExampleText({ text }) {
  return <p className="text-xs text-slate-500">{text}</p>
}

function ModeButton({ active, label: buttonLabel, onClick }) {
  return (
    <button className={`rounded-md border px-3 py-2 text-left text-sm font-semibold ${active ? "border-blue-500 bg-blue-50 text-blue-800" : "border-slate-300 text-slate-700"}`} type="button" onClick={onClick}>
      {buttonLabel}
    </button>
  )
}

function Field({ label: fieldLabel, type = "text", value, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function SelectField({ label: fieldLabel, value, options, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option value={option} key={option}>{label(option)}</option>)}
      </select>
    </label>
  )
}

function TextArea({ label: fieldLabel, plain, value, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <textarea className={`mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-xs ${plain ? "" : "font-mono"}`} value={value} onChange={(event) => onChange(event.target.value)} spellCheck={plain ? undefined : false} />
    </label>
  )
}

function SummaryBlock({ label: blockLabel, value, subvalue }) {
  return (
    <span className="min-w-0">
      <span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">{blockLabel}</span>
      <span className="mt-1 block truncate text-sm font-semibold text-slate-950">{value || "Not set"}</span>
      {subvalue ? <span className="mt-1 block truncate text-xs text-slate-500">{subvalue}</span> : null}
    </span>
  )
}

function buildManualBookingPayload(form) {
  const passengers = valueOrOverride("Passenger snapshot", form.raw_overrides.passengers_json, buildPassengersSnapshot(form.passengers))
  const segments = valueOrOverride("Segment snapshot", form.raw_overrides.segments_json, buildSegmentsSnapshot(form.segments))
  const pricing = valueOrOverride("Pricing snapshot", form.raw_overrides.pricing_json, buildPricingSnapshot(form.pricing))
  const ssr = valueOrOverride("SSR", form.raw_overrides.ssr_json, buildSsrSnapshot(form.ssr))
  const osi = valueOrOverride("OSI", form.raw_overrides.osi_json, buildOsiSnapshot(form.osi))
  const services = valueOrOverride("Services", form.raw_overrides.services_json, buildServicesSnapshot(form.services))
  return {
    source_context: "standalone_manual",
    provider_target: form.provider_target || "manual",
    create_draft_record: true,
    title: form.title || null,
    trip_id: form.trip_id || null,
    client_id: form.client_id || null,
    passenger_ids: passengers.map((item) => item.passenger_id || item.id).filter(Boolean),
    pnr_locator: form.pnr_locator || null,
    passengers_json: asArray(passengers, "Passenger snapshot"),
    segments_json: asArray(segments, "Segment snapshot"),
    pricing_json: asObject(pricing, "Pricing snapshot"),
    ssr_json: asArray(ssr, "SSR"),
    osi_json: asArray(osi, "OSI"),
    services_json: asObject(services, "Services"),
    internal_notes: form.internal_notes || null,
  }
}

function valueOrOverride(labelText, rawValue, fallback) {
  const parsed = parseOptionalJsonOverride(labelText, rawValue)
  return parsed === undefined ? fallback : parsed
}

function parseOptionalJsonOverride(labelText, value) {
  const text = String(value || "").trim()
  if (!text) return undefined
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(`${labelText} raw override must be valid JSON.`)
  }
}

function buildPassengersSnapshot(rows) {
  return rows.map((row, index) => {
    const displayName = [row.first_name, row.last_name].filter(Boolean).join(" ").trim()
    return compactObject({
      id: row.passenger_id || (hasMeaningfulValues(row, ["first_name", "last_name", "date_of_birth", "notes"]) ? `manual-pax-${index + 1}` : ""),
      passenger_id: row.passenger_id,
      passenger_type: row.passenger_type || "adult",
      title: row.title,
      first_name: row.first_name,
      last_name: row.last_name,
      display_name: displayName,
      date_of_birth: row.date_of_birth,
      gender: row.gender,
      nationality: row.nationality,
      notes: row.notes,
    })
  }).filter((item) => hasMeaningfulValues(item, ["passenger_id", "first_name", "last_name", "date_of_birth", "notes"]))
}

function buildSegmentsSnapshot(rows) {
  return rows.map((row, index) => compactObject({
    id: hasMeaningfulValues(row, ["marketing_airline", "flight_number", "departure_airport", "arrival_airport"]) ? `manual-segment-${index + 1}` : "",
    sequence: numberOrNull(row.segment_number) || index + 1,
    segment_number: numberOrNull(row.segment_number) || index + 1,
    marketing_airline_code: row.marketing_airline,
    operating_airline_code: row.operating_airline,
    flight_number: row.flight_number,
    origin_airport_code: row.departure_airport,
    destination_airport_code: row.arrival_airport,
    departure_date: row.departure_date,
    departure_time: row.departure_time,
    departure_datetime: combineDateTime(row.departure_date, row.departure_time),
    arrival_date: row.arrival_date,
    arrival_time: row.arrival_time,
    arrival_datetime: combineDateTime(row.arrival_date, row.arrival_time),
    cabin: row.cabin,
    booking_class: row.booking_class,
    rbd: row.booking_class,
    status_code: row.status_code || "HK",
    aircraft_type: row.aircraft,
    notes: row.notes,
  })).filter((item) => hasMeaningfulValues(item, ["marketing_airline_code", "flight_number", "origin_airport_code", "destination_airport_code", "departure_date", "notes"]))
}

function buildPricingSnapshot(form) {
  const summary = compactObject({
    currency: form.currency || "EUR",
    base_fare_amount: numberOrNull(form.base_fare),
    taxes_amount: numberOrNull(form.taxes),
    fees_amount: numberOrNull(form.fees),
    total_amount: numberOrNull(form.total),
    fare_basis: form.fare_basis,
    tour_code: form.tour_code,
    pricing_notes: form.pricing_notes,
  })
  return Object.keys(summary).length ? { summary } : {}
}

function buildSsrSnapshot(rows) {
  return rows.map((row) => compactObject({
    ssr_code: row.ssr_code,
    airline_code: row.airline,
    passenger_reference: row.passenger_reference,
    segment_reference: row.segment_reference,
    free_text: row.free_text,
    status: row.status,
  })).filter((item) => hasMeaningfulValues(item, ["ssr_code", "free_text"]))
}

function buildOsiSnapshot(rows) {
  return rows.map((row) => compactObject({
    airline_code: row.airline,
    text: row.text,
    passenger_reference: row.passenger_reference,
  })).filter((item) => hasMeaningfulValues(item, ["text"]))
}

function buildServicesSnapshot(rows) {
  const items = rows.map((row) => compactObject({
    service_category: row.service_category,
    service_label: row.service_label,
    passenger_reference: row.passenger_reference,
    segment_reference: row.segment_reference,
    quantity: numberOrNull(row.quantity) || undefined,
    notes: row.notes,
    service_catalogue_id: row.service_catalogue_id,
  })).filter((item) => hasMeaningfulValues(item, ["service_category", "service_label", "notes", "service_catalogue_id"]))
  return items.length ? { items } : {}
}

function compactObject(item) {
  return Object.fromEntries(Object.entries(item).filter(([, value]) => value !== "" && value !== null && value !== undefined))
}

function hasMeaningfulValues(item, keys) {
  return keys.some((key) => String(item[key] || "").trim())
}

function numberOrNull(value) {
  if (value === "" || value === null || value === undefined) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function combineDateTime(dateValue, timeValue) {
  if (!dateValue) return undefined
  return timeValue ? `${dateValue}T${timeValue}:00` : dateValue
}

function asArray(value, labelText) {
  if (Array.isArray(value)) return value
  throw new Error(`${labelText} must be a JSON array.`)
}

function asObject(value, labelText) {
  if (value && typeof value === "object" && !Array.isArray(value)) return value
  if (Array.isArray(value) && labelText === "Services") return { items: value }
  throw new Error(`${labelText} must be a JSON object.`)
}

function tripLabel(item) {
  const trip = item.trip_summary || {}
  return trip.trip_reference || trip.route_summary || item.trip_id || "Trip pending"
}

function offerLabel(item) {
  const workspace = item.offer_workspace_summary || item.workspace_summary || {}
  return workspace.title || workspace.id || item.workspace_id || "Offer workspace"
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function dateLabel(value) {
  return value ? new Date(value).toLocaleDateString() : "Not set"
}
