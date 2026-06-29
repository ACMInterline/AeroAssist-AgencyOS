import { useEffect, useMemo, useState } from "react"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import Columns3 from "lucide-react/dist/esm/icons/columns-3.js"
import Copy from "lucide-react/dist/esm/icons/copy.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCcw from "lucide-react/dist/esm/icons/refresh-ccw.js"
import Save from "lucide-react/dist/esm/icons/save.js"
import Wand2 from "lucide-react/dist/esm/icons/wand-2.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const emptyOption = { label: "New option", option_type: "flight", main_airline_code: "", provider_name: "manual" }
const emptySegment = { sequence: 1, marketing_airline_code: "", operating_airline_code: "", flight_number: "", origin_airport: "", destination_airport: "", departure_at: "", arrival_at: "", aircraft_type: "", cabin_class: "economy", booking_class: "", fare_basis: "" }
const emptyFare = { fare_family_name: "", cabin_class: "economy", booking_class: "", included_baggage_json: "{}" }
const emptyPrice = { line_type: "base_fare", label: "", amount: "", currency: "EUR" }

export default function OfferBuilderPage({ workspaceId }) {
  const [state, setState] = useState(null)
  const [selectedOptionId, setSelectedOptionId] = useState("")
  const [optionForm, setOptionForm] = useState(emptyOption)
  const [segmentForm, setSegmentForm] = useState(emptySegment)
  const [fareForm, setFareForm] = useState(emptyFare)
  const [priceForm, setPriceForm] = useState(emptyPrice)
  const [editForm, setEditForm] = useState({ label: "", main_airline_code: "", internal_notes: "" })
  const [acceptCandidate, setAcceptCandidate] = useState(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load(preferredOptionId = selectedOptionId) {
    const context = await loadCurrentAgency()
    const [detail, comparison, acceptance] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/offer-workspaces/${workspaceId}`),
      apiGet(`/api/agencies/${context.agency.id}/offer-workspaces/${workspaceId}/comparison`),
      apiGet(`/api/agencies/${context.agency.id}/offer-workspaces/${workspaceId}/acceptance`),
    ])
    const readiness = acceptance.booking_readiness
    const bookingWorkspaces = readiness?.trip_id
      ? await apiGet(`/api/agencies/${context.agency.id}/booking-workspaces?trip_id=${encodeURIComponent(readiness.trip_id)}`)
      : { items: [] }
    const urlOption = new URLSearchParams(window.location.search).get("option")
    const nextSelected = preferredOptionId || urlOption || detail.options?.[0]?.id || ""
    setState({ ...context, ...detail, matrix: comparison.matrix, acceptance, bookingWorkspaces: bookingWorkspaces.items || [] })
    setSelectedOptionId(nextSelected)
    const selected = detail.options?.find((option) => option.id === nextSelected) || detail.options?.[0]
    if (selected) {
      setEditForm({
        label: selected.label || "",
        main_airline_code: selected.main_airline_code || "",
        internal_notes: selected.internal_notes || "",
      })
      setSegmentForm((current) => ({
        ...current,
        sequence: (detail.segments || []).filter((segment) => segment.option_id === selected.id).length + 1,
        marketing_airline_code: selected.main_airline_code || current.marketing_airline_code,
      }))
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [workspaceId])

  const selectedOption = (state?.options || []).find((option) => option.id === selectedOptionId)
  const grouped = useMemo(() => {
    const optionId = selectedOption?.id
    return {
      segments: (state?.segments || []).filter((item) => item.option_id === optionId),
      fareBundles: (state?.fare_bundles || []).filter((item) => item.option_id === optionId),
      pricingLines: (state?.pricing_lines || []).filter((item) => item.option_id === optionId),
    }
  }, [selectedOption, state])

  function setNested(setter, name, value) {
    setter((current) => ({ ...current, [name]: value }))
  }

  function parseJson(value) {
    const trimmed = String(value || "").trim()
    return trimmed ? JSON.parse(trimmed) : {}
  }

  function payloadWithoutBlanks(payload) {
    return Object.fromEntries(Object.entries(payload).map(([key, value]) => [key, value === "" ? null : value]))
  }

  async function addOption(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/offer-workspaces/${workspaceId}/options`, payloadWithoutBlanks(optionForm))
      setOptionForm(emptyOption)
      setMessage("Option added.")
      await load(result.option.id)
    } catch (err) {
      setError(err.message)
    }
  }

  async function saveOption(event) {
    event.preventDefault()
    if (!selectedOption) return
    await apiPut(`/api/agencies/${state.agency.id}/offer-options/${selectedOption.id}`, payloadWithoutBlanks(editForm))
    setMessage("Option saved.")
    await load(selectedOption.id)
  }

  async function cloneOption() {
    if (!selectedOption) return
    const result = await apiPost(`/api/agencies/${state.agency.id}/offer-options/${selectedOption.id}/clone`)
    setMessage("Option cloned.")
    await load(result.option.id)
  }

  async function addSegment(event) {
    event.preventDefault()
    if (!selectedOption) return
    const payload = payloadWithoutBlanks({ ...segmentForm, sequence: Number(segmentForm.sequence || 1) })
    await apiPost(`/api/agencies/${state.agency.id}/offer-options/${selectedOption.id}/segments`, payload)
    setSegmentForm({ ...emptySegment, sequence: grouped.segments.length + 2, marketing_airline_code: selectedOption.main_airline_code || "" })
    setMessage("Segment added.")
    await load(selectedOption.id)
  }

  async function addFareBundle(event) {
    event.preventDefault()
    if (!selectedOption) return
    const payload = payloadWithoutBlanks({
      fare_family_name: fareForm.fare_family_name,
      cabin_class: fareForm.cabin_class,
      booking_class: fareForm.booking_class,
      included_baggage_json: parseJson(fareForm.included_baggage_json),
    })
    await apiPost(`/api/agencies/${state.agency.id}/offer-options/${selectedOption.id}/fare-bundles`, payload)
    setFareForm(emptyFare)
    setMessage("Fare bundle added.")
    await load(selectedOption.id)
  }

  async function addPricingLine(event) {
    event.preventDefault()
    if (!selectedOption) return
    await apiPost(`/api/agencies/${state.agency.id}/offer-options/${selectedOption.id}/pricing-lines`, {
      line_type: priceForm.line_type,
      label: priceForm.label,
      amount: Number(priceForm.amount || 0),
      currency: priceForm.currency || state.workspace.currency || "EUR",
    })
    setPriceForm({ ...emptyPrice, currency: state.workspace.currency || "EUR" })
    setMessage("Pricing line added.")
    await load(selectedOption.id)
  }

  async function recalculatePricing() {
    if (!selectedOption) return
    await apiPost(`/api/agencies/${state.agency.id}/offer-options/${selectedOption.id}/recalculate-pricing`)
    setMessage("Pricing recalculated.")
    await load(selectedOption.id)
  }

  async function evaluateRules() {
    if (!selectedOption) return
    await apiPost(`/api/agencies/${state.agency.id}/offer-options/${selectedOption.id}/evaluate-rules`)
    setMessage("Rules evaluated.")
    await load(selectedOption.id)
  }

  async function recommendOption() {
    if (!selectedOption) return
    await apiPost(`/api/agencies/${state.agency.id}/offer-workspaces/${workspaceId}/recommend`, { option_id: selectedOption.id, tag: "Recommended", rank: 1 })
    setMessage("Recommendation saved.")
    await load(selectedOption.id)
  }

  async function acceptOption() {
    if (!acceptCandidate) return
    setError("")
    setMessage("")
    try {
      await apiPost(
        `/api/agencies/${state.agency.id}/offer-workspaces/${workspaceId}/options/${acceptCandidate.id}/accept`,
        {
          acceptance_source: "internal",
          provider_target: "manual",
        },
      )
      setAcceptCandidate(null)
      setMessage("Offer accepted. The trip accepted-offer snapshot and booking readiness package were refreshed.")
      await load(acceptCandidate.id)
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
      const readinessId = state?.acceptance?.booking_readiness?.id
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

  const pricing = selectedOption?.pricing_summary_json || {}
  const acceptedOptionId = state?.acceptance?.acceptance?.option_id

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <a className="text-sm font-medium text-blue-700" href={`/agency/offers/${workspaceId}`}>Back to workspace</a>
                <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state?.workspace?.status?.replaceAll("_", " ")} · {state?.workspace?.currency}</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">{state?.workspace?.title}</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={cloneOption} disabled={!selectedOption}>
                  <Copy className="h-4 w-4" />
                  Clone
                </button>
                <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={recalculatePricing} disabled={!selectedOption}>
                  <RefreshCcw className="h-4 w-4" />
                  Price
                </button>
                <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={evaluateRules} disabled={!selectedOption}>
                  <Wand2 className="h-4 w-4" />
                  Rules
                </button>
                <button className="aa-primary-action inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={recommendOption} disabled={!selectedOption}>
                  <CheckCircle2 className="h-4 w-4" />
                  Recommend
                </button>
                <button
                  className="aa-primary-action inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold"
                  type="button"
                  onClick={() => setAcceptCandidate(selectedOption)}
                  disabled={!selectedOption || selectedOption?.id === acceptedOptionId}
                >
                  <CheckCircle2 className="h-4 w-4" />
                  {selectedOption?.id === acceptedOptionId ? "Accepted" : "Accept"}
                </button>
                {state?.acceptance?.booking_readiness ? (
                  <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={createOrOpenBookingWorkspace}>
                    Booking Workspace
                  </button>
                ) : null}
              </div>
            </div>
          </div>

          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-4 xl:grid-cols-[300px_minmax(0,1fr)_360px]">
            <aside className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addOption}>
                <h3 className="font-semibold text-slate-950">Options</h3>
                <Field label="Label"><input value={optionForm.label} onChange={(event) => setNested(setOptionForm, "label", event.target.value)} /></Field>
                <Field label="Type">
                  <select value={optionForm.option_type} onChange={(event) => setNested(setOptionForm, "option_type", event.target.value)}>
                    {["flight", "package", "service_only", "manual"].map((value) => <option value={value} key={value}>{value.replaceAll("_", " ")}</option>)}
                  </select>
                </Field>
                <Field label="Airline"><input value={optionForm.main_airline_code} onChange={(event) => setNested(setOptionForm, "main_airline_code", event.target.value.toUpperCase())} maxLength={3} /></Field>
                <button className="aa-primary-action inline-flex w-full items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-semibold" type="submit"><Plus className="h-4 w-4" />Add</button>
              </form>

              <div className="rounded-lg border border-slate-200 bg-white">
                {(state?.options || []).length ? state.options.map((option) => (
                  <button className={`flex w-full items-start justify-between gap-3 border-b border-slate-100 px-4 py-3 text-left last:border-b-0 ${selectedOptionId === option.id ? "bg-blue-50" : "hover:bg-slate-50"}`} type="button" onClick={() => {
                    setSelectedOptionId(option.id)
                    setEditForm({ label: option.label || "", main_airline_code: option.main_airline_code || "", internal_notes: option.internal_notes || "" })
                  }} key={option.id}>
                    <span>
                      <span className="block font-semibold text-slate-950">{option.label}</span>
                      <span className="block text-xs text-slate-500">
                        {option.id === acceptedOptionId ? "accepted" : option.status?.replaceAll("_", " ")}
                        {" · "}
                        {money((option.pricing_summary_json || {}).total_amount, (option.pricing_summary_json || {}).currency)}
                      </span>
                    </span>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">{option.main_airline_code || "TBD"}</span>
                  </button>
                )) : <div className="p-5"><EmptyState title="No options" body="Add an option to begin." /></div>}
              </div>
            </aside>

            <main className="space-y-4">
              {selectedOption ? (
                <>
                  <form className="grid gap-3 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-3" onSubmit={saveOption}>
                    <Field label="Option label"><input value={editForm.label} onChange={(event) => setNested(setEditForm, "label", event.target.value)} /></Field>
                    <Field label="Main airline"><input value={editForm.main_airline_code} onChange={(event) => setNested(setEditForm, "main_airline_code", event.target.value.toUpperCase())} maxLength={3} /></Field>
                    <div className="flex items-end">
                      <button className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit"><Save className="h-4 w-4" />Save</button>
                    </div>
                    <label className="grid gap-1 text-sm font-medium text-slate-700 md:col-span-3">Internal notes<textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={editForm.internal_notes} onChange={(event) => setNested(setEditForm, "internal_notes", event.target.value)} /></label>
                  </form>

                  <section className="grid gap-4 md:grid-cols-4">
                    <Metric label="Total" value={money(pricing.total_amount, pricing.currency)} />
                    <Metric label="Rules" value={(selectedOption.rules_summary_json?.status || "pending").replaceAll("_", " ")} />
                    <Metric label="Services" value={(selectedOption.service_feasibility_json?.overall_status || "pending").replaceAll("_", " ")} />
                    <Metric label="Warnings" value={selectedOption.warnings_json?.length || 0} />
                  </section>

                  <section className="grid gap-4 lg:grid-cols-2">
                    <RecordPanel title="Segments" items={grouped.segments} empty="No segments" render={(segment) => `${segment.sequence}. ${segment.origin_airport} to ${segment.destination_airport} · ${segment.marketing_airline_code}${segment.flight_number ? ` ${segment.flight_number}` : ""} · ${segment.cabin_class || "cabin pending"}`} />
                    <RecordPanel title="Fare Bundles" items={grouped.fareBundles} empty="No fare bundles" render={(bundle) => `${bundle.fare_family_name} · ${bundle.cabin_class}${bundle.booking_class ? ` · ${bundle.booking_class}` : ""}`} />
                  </section>
                  <RecordPanel title="Pricing Lines" items={grouped.pricingLines} empty="No pricing lines" render={(line) => `${line.line_type.replaceAll("_", " ")} · ${line.label} · ${money(line.amount, line.currency)}`} />
                  <WarningsPanel option={selectedOption} />
                  <MiniMatrix matrix={state.matrix} selectedOptionId={selectedOption.id} />
                </>
              ) : (
                <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8">
                  <EmptyState title="Select an option" body="Create or select an option to edit details." />
                </div>
              )}
            </main>

            <aside className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addSegment}>
                <h3 className="font-semibold text-slate-950">Add Segment</h3>
                <div className="grid grid-cols-[80px_1fr] gap-2">
                  <Field label="Seq"><input type="number" min="1" value={segmentForm.sequence} onChange={(event) => setNested(setSegmentForm, "sequence", event.target.value)} /></Field>
                  <Field label="Airline"><input value={segmentForm.marketing_airline_code} onChange={(event) => setNested(setSegmentForm, "marketing_airline_code", event.target.value.toUpperCase())} maxLength={3} /></Field>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Origin"><input value={segmentForm.origin_airport} onChange={(event) => setNested(setSegmentForm, "origin_airport", event.target.value.toUpperCase())} maxLength={3} /></Field>
                  <Field label="Destination"><input value={segmentForm.destination_airport} onChange={(event) => setNested(setSegmentForm, "destination_airport", event.target.value.toUpperCase())} maxLength={3} /></Field>
                </div>
                <Field label="Flight"><input value={segmentForm.flight_number} onChange={(event) => setNested(setSegmentForm, "flight_number", event.target.value)} /></Field>
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Cabin"><input value={segmentForm.cabin_class} onChange={(event) => setNested(setSegmentForm, "cabin_class", event.target.value)} /></Field>
                  <Field label="Booking"><input value={segmentForm.booking_class} onChange={(event) => setNested(setSegmentForm, "booking_class", event.target.value.toUpperCase())} /></Field>
                </div>
                <button className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit" disabled={!selectedOption}><Plus className="h-4 w-4" />Add Segment</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addFareBundle}>
                <h3 className="font-semibold text-slate-950">Add Fare Bundle</h3>
                <Field label="Family"><input value={fareForm.fare_family_name} onChange={(event) => setNested(setFareForm, "fare_family_name", event.target.value)} /></Field>
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Cabin"><input value={fareForm.cabin_class} onChange={(event) => setNested(setFareForm, "cabin_class", event.target.value)} /></Field>
                  <Field label="Booking"><input value={fareForm.booking_class} onChange={(event) => setNested(setFareForm, "booking_class", event.target.value.toUpperCase())} /></Field>
                </div>
                <label className="grid gap-1 text-sm font-medium text-slate-700">Baggage JSON<textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2 font-mono text-xs font-normal" value={fareForm.included_baggage_json} onChange={(event) => setNested(setFareForm, "included_baggage_json", event.target.value)} /></label>
                <button className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit" disabled={!selectedOption}><Plus className="h-4 w-4" />Add Fare</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addPricingLine}>
                <h3 className="font-semibold text-slate-950">Add Pricing Line</h3>
                <Field label="Type">
                  <select value={priceForm.line_type} onChange={(event) => setNested(setPriceForm, "line_type", event.target.value)}>
                    {["base_fare", "tax", "surcharge", "service_fee", "commission", "discount", "ancillary", "other"].map((value) => <option value={value} key={value}>{value.replaceAll("_", " ")}</option>)}
                  </select>
                </Field>
                <Field label="Label"><input value={priceForm.label} onChange={(event) => setNested(setPriceForm, "label", event.target.value)} /></Field>
                <div className="grid grid-cols-[1fr_90px] gap-2">
                  <Field label="Amount"><input type="number" step="0.01" value={priceForm.amount} onChange={(event) => setNested(setPriceForm, "amount", event.target.value)} /></Field>
                  <Field label="Currency"><input value={priceForm.currency} onChange={(event) => setNested(setPriceForm, "currency", event.target.value.toUpperCase())} maxLength={3} /></Field>
                </div>
                <button className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit" disabled={!selectedOption}><Plus className="h-4 w-4" />Add Price</button>
              </form>
            </aside>
          </section>
          <AcceptModal
            option={acceptCandidate}
            grouped={grouped}
            onCancel={() => setAcceptCandidate(null)}
            onConfirm={acceptOption}
          />
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Field({ label, children }) {
  return (
    <label className="grid gap-1 text-sm font-medium text-slate-700">
      {label}
      {children.type === "select"
        ? <select {...children.props} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" />
        : <input {...children.props} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" />}
    </label>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-lg font-semibold text-slate-950">{value}</p></div>
}

function RecordPanel({ title, items, empty, render }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      {items?.length ? <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>)}</div> : <div className="mt-4"><EmptyState title={empty} body="Records appear here when added." /></div>}
    </section>
  )
}

function WarningsPanel({ option }) {
  const warnings = option.warnings_json || []
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">Warnings</h3>
      {warnings.length ? (
        <div className="mt-4 space-y-2">
          {warnings.map((warning, index) => <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900" key={`${warning.message}-${index}`}>{warning.message || JSON.stringify(warning)}</p>)}
        </div>
      ) : <p className="mt-4 text-sm text-slate-500">No warnings recorded.</p>}
    </section>
  )
}

function MiniMatrix({ matrix, selectedOptionId }) {
  const column = matrix?.columns?.find((entry) => entry.option_id === selectedOptionId)
  if (!matrix?.rows?.length || !column) return null
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-2">
        <Columns3 className="h-4 w-4 text-blue-700" />
        <h3 className="font-semibold text-slate-950">Comparison Column</h3>
      </div>
      <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
        {matrix.rows.map((row) => (
          <div className="grid grid-cols-[150px_minmax(0,1fr)] gap-3 p-3 text-sm" key={row.key}>
            <span className="font-medium text-slate-700">{row.label}</span>
            <span className="text-slate-600">{displayValue(row.values?.[selectedOptionId])}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

function AcceptModal({ option, grouped, onCancel, onConfirm }) {
  if (!option) return null
  const pricing = option.pricing_summary_json || {}
  const fare = grouped.fareBundles?.[0]
  const route = grouped.segments?.length
    ? grouped.segments.map((segment) => `${segment.origin_airport}-${segment.destination_airport}`).join(" / ")
    : "Route pending"
  const warnings = option.warnings_json || []
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <section className="w-full max-w-xl rounded-lg border border-slate-200 bg-white p-5 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-950">Accept Option</h3>
        <div className="mt-4 space-y-3 text-sm text-slate-700">
          <p>
            <span className="font-semibold text-slate-950">{option.label}</span>
          </p>
          <p>Pricing: {money(pricing.total_amount, pricing.currency)}</p>
          <p>Route: {route}</p>
          <p>Fare bundle: {fare ? `${fare.fare_family_name} · ${fare.cabin_class}` : "Fare bundle pending"}</p>
          <p>Warnings: {warnings.length}</p>
          <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
            Acceptance creates or updates the trip operational baseline and booking readiness package. It does not
            create a live booking, PNR, ticket, EMD, invoice, or supplier action.
          </p>
        </div>
        <div className="mt-5 flex flex-wrap justify-end gap-2">
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onCancel}>
            Cancel
          </button>
          <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={onConfirm}>
            Accept option
          </button>
        </div>
      </section>
    </div>
  )
}

function money(amount, currency) {
  if (amount === null || amount === undefined || amount === "") return "Not priced"
  return `${Number(amount).toFixed(2)} ${currency || "EUR"}`
}

function displayValue(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  if (typeof value === "boolean") return value ? "Yes" : "No"
  return String(value)
}
