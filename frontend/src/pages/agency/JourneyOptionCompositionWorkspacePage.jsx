import { useEffect, useMemo, useState } from "react"
import Archive from "lucide-react/dist/esm/icons/archive.js"
import ArrowDown from "lucide-react/dist/esm/icons/arrow-down.js"
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import ArrowUp from "lucide-react/dist/esm/icons/arrow-up.js"
import Check from "lucide-react/dist/esm/icons/check.js"
import CircleDollarSign from "lucide-react/dist/esm/icons/circle-dollar-sign.js"
import Copy from "lucide-react/dist/esm/icons/copy.js"
import GitCompareArrows from "lucide-react/dist/esm/icons/git-compare-arrows.js"
import History from "lucide-react/dist/esm/icons/history.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import Save from "lucide-react/dist/esm/icons/save.js"
import ShieldAlert from "lucide-react/dist/esm/icons/shield-alert.js"
import Sparkles from "lucide-react/dist/esm/icons/sparkles.js"
import Undo2 from "lucide-react/dist/esm/icons/undo-2.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const emptyFare = { external_brand_name: "", client_safe_label: "", airline_code: "", cabin: "", booking_class: "", fare_basis: "", baggage_summary: "", carry_on_summary: "", changeability: "unknown", refundability: "unknown", client_visible_highlights: "", internal_agent_notes: "" }
const emptyPrice = { currency: "EUR", base_amount: "", tax_amount: "", ancillary_amount: "", service_fee: "", ticketing_fee: "", assistance_fee: "", markup_amount: "", discount_amount: "", total_selling_amount: "", validity_until: "" }

export default function JourneyOptionCompositionWorkspacePage() {
  const [state, setState] = useState(null)
  const [compositions, setCompositions] = useState([])
  const [detail, setDetail] = useState(null)
  const [canonical, setCanonical] = useState(null)
  const [selectedId, setSelectedId] = useState("")
  const [selectedOptionId, setSelectedOptionId] = useState("")
  const [selectedSegments, setSelectedSegments] = useState([])
  const [fareLibrary, setFareLibrary] = useState([])
  const [manualFare, setManualFare] = useState(emptyFare)
  const [price, setPrice] = useState(emptyPrice)
  const [selectedFareId, setSelectedFareId] = useState("")
  const [optionDraft, setOptionDraft] = useState({ client_safe_label: "", internal_notes: "" })
  const [comparison, setComparison] = useState(null)
  const [handoff, setHandoff] = useState(null)
  const [offerId, setOfferId] = useState("")
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const query = useMemo(() => new URLSearchParams(window.location.search), [])

  async function load(preferredId = selectedId) {
    const context = await loadCurrentAgency()
    const response = await apiGet(`/api/agencies/${context.agency.id}/journey-option-compositions?include_archived=true`)
    const queryId = query.get("composition_id")
    const journeyId = query.get("journey_id")
    const match = journeyId ? response.items?.find((item) => item.journey_id === journeyId && !item.archived_at) : null
    const nextId = preferredId || queryId || match?.id || response.items?.find((item) => !item.archived_at)?.id || response.items?.[0]?.id || ""
    const library = await apiGet(`/api/agencies/${context.agency.id}/fare-brand-library`).catch(() => ({ fare_families: [] }))
    setState(context)
    setCompositions(response.items || [])
    setFareLibrary(library.fare_families || [])
    setSelectedId(nextId)
    if (nextId) await loadDetail(context.agency.id, nextId)
    else { setDetail(null); setCanonical(null) }
  }

  async function loadDetail(agencyId, compositionId) {
    const response = await apiGet(`/api/agencies/${agencyId}/journey-option-compositions/${compositionId}`)
    const journey = await apiGet(`/api/agencies/${agencyId}/journeys/${response.composition.journey_id}`)
    setDetail(response)
    setCanonical(journey)
    const nextOption = response.options?.find((item) => !item.archived_at)?.id || ""
    setSelectedOptionId((current) => response.options?.some((item) => item.id === current && !item.archived_at) ? current : nextOption)
    setComparison(response.comparison_results?.[0] || null)
    setOfferId(response.composition.offer_workspace_id || response.composition.offer_id || query.get("offer_id") || "")
  }

  useEffect(() => { load().catch(fail(setError)) }, [])

  async function refresh() {
    await loadDetail(state.agency.id, selectedId)
    const response = await apiGet(`/api/agencies/${state.agency.id}/journey-option-compositions?include_archived=true`)
    setCompositions(response.items || [])
  }

  async function createFromJourney() {
    const journeyId = query.get("journey_id") || canonical?.journey?.id
    if (!journeyId) throw new Error("Open this workspace from a Journey or select an existing composition.")
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-option-compositions/from-journey/${journeyId}`, {})
    setNotice("Composition created from canonical Journey segments. No offer was published or sent.")
    setSelectedId(response.composition.id)
    await load(response.composition.id)
  }

  async function addOption() {
    const response = await apiPost(base(), {})
    setSelectedOptionId(response.option.id)
    setNotice(`${response.option.client_safe_label} added.`)
    await refresh()
  }

  async function cloneOption(optionId) {
    const response = await apiPost(`${base()}/${optionId}/clone`, {})
    setSelectedOptionId(response.option.id)
    setNotice("Option cloned with references retained. Canonical segments were not duplicated.")
    await refresh()
  }

  async function moveOption(optionId, direction) {
    const active = activeOptions()
    const index = active.findIndex((item) => item.id === optionId)
    const target = index + direction
    if (target < 0 || target >= active.length) return
    const ids = active.map((item) => item.id)
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    await apiPost(`/api/agencies/${state.agency.id}/journey-option-compositions/${selectedId}/options/reorder`, { option_ids: ids })
    await refresh()
  }

  async function archiveOption(optionId) {
    await apiPost(`${base()}/${optionId}/archive`, {})
    setNotice("Option archived without deleting historical metadata.")
    await refresh()
  }

  async function restoreOption(optionId) {
    await apiPost(`${base()}/${optionId}/restore`, {})
    await refresh()
  }

  async function assignSegments() {
    if (!selectedOptionId || !selectedSegments.length) return
    await apiPost(`${base()}/${selectedOptionId}/segments`, { segment_ids: selectedSegments })
    setSelectedSegments([])
    setNotice("Canonical Journey segments assigned by reference and metrics recalculated.")
    await refresh()
  }

  async function addManualFare() {
    if (!selectedOptionId) return
    const response = await apiPost(`${base()}/${selectedOptionId}/fare-brands`, cleanFare(manualFare))
    setSelectedFareId(response.fare_brand_choice.id)
    setManualFare(emptyFare)
    setNotice("Manual fare choice added with review-required provenance.")
    await refresh()
  }

  async function importFare(fareFamilyId) {
    if (!selectedOptionId || !fareFamilyId) return
    const response = await apiPost(`${base()}/${selectedOptionId}/fare-brands/import`, { fare_family_id: fareFamilyId })
    setSelectedFareId(response.fare_brand_choice.id)
    setNotice("Published fare-brand intelligence imported with evidence and uncertainty states.")
    await refresh()
  }

  async function duplicateFare(fareId) {
    const response = await apiPost(`${base()}/${selectedOptionId}/fare-brands/${fareId}/clone`, {})
    setSelectedFareId(response.fare_brand_choice.id)
    setNotice("Fare choice duplicated with its commercial metadata and provenance retained.")
    await refresh()
  }

  async function moveFare(fareId, direction) {
    const index = selectedFares.findIndex((item) => item.id === fareId)
    const target = index + direction
    if (target < 0 || target >= selectedFares.length) return
    const ids = selectedFares.map((item) => item.id)
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    await apiPost(`${base()}/${selectedOptionId}/fare-brands/reorder`, { fare_choice_ids: ids })
    await refresh()
  }

  async function archiveFare(fareId) {
    await apiPost(`${base()}/${selectedOptionId}/fare-brands/${fareId}/archive`, {})
    if (selectedFareId === fareId) setSelectedFareId("")
    setNotice("Fare choice archived without deleting historical metadata.")
    await refresh()
  }

  async function restoreFare(fareId) {
    await apiPost(`${base()}/${selectedOptionId}/fare-brands/${fareId}/restore`, {})
    await refresh()
  }

  async function saveOptionMetadata() {
    await apiPut(`${base()}/${selectedOptionId}`, clean(optionDraft))
    setNotice("Client-facing option title and internal note saved separately.")
    await refresh()
  }

  async function savePrice() {
    if (!selectedOptionId || !selectedFareId) throw new Error("Select a fare choice before saving pricing.")
    const payload = numericPrice(clean(price))
    const response = await apiPut(`${base()}/${selectedOptionId}/fare-brands/${selectedFareId}/pricing`, payload)
    setPrice({ ...emptyPrice, currency: response.price_breakdown.currency, total_selling_amount: String(response.price_breakdown.total_selling_amount) })
    setNotice("Commercial values saved after deterministic arithmetic validation.")
    await refresh()
  }

  async function assessServices() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-option-compositions/${selectedId}/assess-services`, {})
    setNotice(`${response.count} advisory service assessments projected. Airline acceptance was not guaranteed.`)
    await refresh()
  }

  async function compareOptions() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-option-compositions/${selectedId}/compare`, {})
    setComparison(response.comparison_result)
    setNotice("Deterministic comparison generated. No automatic recommendation was asserted.")
    await refresh()
  }

  async function selectPreferred(optionId, fareId) {
    await apiPost(`/api/agencies/${state.agency.id}/journey-option-compositions/${selectedId}/preferred-option`, { option_id: optionId, fare_choice_id: fareId || undefined, client_rationale: "Selected by the travel agent after review." })
    setNotice("Preferred option recorded as an explicit agent decision.")
    await refresh()
  }

  async function createSnapshot() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-option-compositions/${selectedId}/snapshots`, { finalize: true })
    setNotice(`Immutable composition snapshot ${response.snapshot.snapshot_number} created.`)
    await refresh()
  }

  async function previewHandoff() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-option-compositions/${selectedId}/offer-handoff/preview`, clean({ offer_workspace_id: offerId }))
    setHandoff(response)
  }

  async function applyHandoff() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-option-compositions/${selectedId}/offer-handoff/apply`, { offer_workspace_id: offerId })
    setHandoff(response)
    setNotice("Composition snapshot linked to the offer workspace. No offer record or provider system was mutated.")
    await refresh()
  }

  function base() { return `/api/agencies/${state.agency.id}/journey-option-compositions/${selectedId}/options` }
  function activeOptions() { return (detail?.options || []).filter((item) => !item.archived_at) }
  const activeOption = activeOptions().find((item) => item.id === selectedOptionId)
  const availableSegments = (canonical?.segments || []).filter((segment) => !(detail?.segment_assignments || []).some((assignment) => assignment.option_id === selectedOptionId && assignment.source_segment_id === segment.id && assignment.included && !assignment.archived_at))
  const selectedFares = (detail?.fare_brand_choices || []).filter((item) => item.option_id === selectedOptionId && !item.archived_at)
  const archivedFares = (detail?.fare_brand_choices || []).filter((item) => item.option_id === selectedOptionId && item.archived_at)
  const journey = detail?.journey
  const composition = detail?.composition

  useEffect(() => {
    setOptionDraft({ client_safe_label: activeOption?.client_safe_label || "", internal_notes: activeOption?.internal_notes || "" })
  }, [activeOption?.id, activeOption?.updated_at])

  return <AgencyLayout user={state?.me?.user} agency={state?.agency}>
    <ProtectedRoute loading={!state && !error} error={error}>
      <div className="space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm font-semibold uppercase text-blue-700">Offer Preparation</p><h1 className="mt-2 text-2xl font-semibold text-slate-950">Journey Option Composition</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Build itinerary alternatives and fare-brand choices from canonical Journey segments and governed knowledge. No live price, availability, publication, booking, ticketing, provider contact, or EMD action runs here.</p></div><div className="flex gap-2"><button type="button" title="Create from Journey" onClick={() => createFromJourney().catch(fail(setError))} className="icon-button"><Plus className="h-4 w-4" /></button><button type="button" title="Refresh workspace" onClick={() => load().catch(fail(setError))} className="icon-button"><RefreshCw className="h-4 w-4" /></button></div></header>

        {notice ? <div className="border-y border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div> : null}
        {error ? <div className="border-y border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><Metric label="Compositions" value={compositions.length} /><Metric label="Options" value={activeOptions().length} /><Metric label="Fare choices" value={(detail?.fare_brand_choices || []).filter((item) => !item.archived_at).length} /><Metric label="Completeness" value={`${composition?.completeness_score || 0}%`} /><Metric label="Review" value={composition?.requires_review ? "Required" : "Clear"} warning={composition?.requires_review} /></section>

        <div className="grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
          <aside><div className="flex justify-between"><h2 className="font-semibold text-slate-950">Composition versions</h2><span className="text-sm text-slate-500">{compositions.length}</span></div><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{compositions.map((item) => <button key={item.id} type="button" onClick={() => { setSelectedId(item.id); loadDetail(state.agency.id, item.id).catch(fail(setError)) }} className={`block w-full px-2 py-3 text-left ${item.id === selectedId ? "bg-blue-50" : "hover:bg-slate-50"}`}><p className="font-semibold text-slate-950">{item.client_safe_title || item.title}</p><p className="mt-1 text-xs text-slate-500">Version {item.version_number} · {title(item.status)}</p></button>)}</div></aside>

          {composition ? <main className="min-w-0 space-y-8">
            <section className="border-b border-slate-200 pb-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-slate-500">{journey?.journey_reference}</p><h2 className="mt-1 text-xl font-semibold text-slate-950">{composition.client_safe_title || composition.title}</h2><p className="mt-2 text-2xl font-semibold text-slate-950">{journey?.origin_airport_code || "Unknown"} <ArrowRight className="mx-2 inline h-5 w-5 text-slate-400" /> {journey?.destination_airport_code || "Unknown"}</p><p className="mt-2 text-sm text-slate-600">{date(journey?.departure_date)} · {(journey?.passenger_ids || []).length || "Unknown"} passengers · {title(composition.status)}</p></div><div className="flex flex-wrap gap-2"><button type="button" onClick={() => createSnapshot().catch(fail(setError))} className="secondary-button"><History className="h-4 w-4" />Create snapshot</button><button type="button" onClick={() => previewHandoff().catch(fail(setError))} className="primary-button"><Sparkles className="h-4 w-4" />Prepare for offer</button></div></div></section>

            <section><div className="flex flex-wrap items-end justify-between gap-3"><div><h3 className="text-lg font-semibold text-slate-950">Itinerary option board</h3><p className="mt-1 text-sm text-slate-600">The default target is three route alternatives with three prominent fare choices each.</p></div><button type="button" onClick={() => addOption().catch(fail(setError))} className="secondary-button"><Plus className="h-4 w-4" />Add option</button></div><div className="mt-4 grid gap-4 lg:grid-cols-3">{activeOptions().map((option) => <OptionCard key={option.id} option={option} detail={detail} selected={option.id === selectedOptionId} onSelect={setSelectedOptionId} onClone={cloneOption} onMove={moveOption} onArchive={archiveOption} onPreferred={selectPreferred} onError={setError} />)}</div>{!activeOptions().length ? <EmptyState title="No options yet" body="Add an option, then assign canonical Journey segments without retyping them." /> : null}</section>

            {activeOption ? <section><div className="flex items-center gap-2"><Save className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Option presentation</h3></div><div className="mt-3 grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)_auto]"><input value={optionDraft.client_safe_label} onChange={(event) => setOptionDraft({ ...optionDraft, client_safe_label: event.target.value })} placeholder="Client-facing option title" className="field" /><input value={optionDraft.internal_notes} onChange={(event) => setOptionDraft({ ...optionDraft, internal_notes: event.target.value })} placeholder="Internal agent note" className="field" /><button type="button" onClick={() => saveOptionMetadata().catch(fail(setError))} className="secondary-button"><Save className="h-4 w-4" />Save</button></div></section> : null}

            {activeOption ? <section className="grid gap-7 xl:grid-cols-2"><div><div className="flex items-center gap-2"><Plane className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Assign canonical segments to {activeOption.client_safe_label}</h3></div><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{availableSegments.map((segment) => <label key={segment.id} className="flex items-center gap-3 py-3 text-sm"><input type="checkbox" checked={selectedSegments.includes(segment.id)} onChange={(event) => setSelectedSegments(event.target.checked ? [...selectedSegments, segment.id] : selectedSegments.filter((id) => id !== segment.id))} /><span className="font-semibold text-slate-900">{segment.marketing_carrier_code || "?"} {segment.marketing_flight_number || ""}</span><span className="text-slate-600">{segment.origin_airport_code || "???"} to {segment.destination_airport_code || "???"}</span></label>)}{!availableSegments.length ? <p className="py-4 text-sm text-slate-500">All canonical segments are already assigned to this option or the Journey has none.</p> : null}</div><button type="button" onClick={() => assignSegments().catch(fail(setError))} disabled={!selectedSegments.length} className="mt-3 primary-button"><Check className="h-4 w-4" />Assign selected</button></div>

              <div><div className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Fare-brand choices</h3></div><select defaultValue="" onChange={(event) => { importFare(event.target.value).catch(fail(setError)); event.target.value = "" }} className="field mt-3"><option value="">Import published fare brand...</option>{fareLibrary.map((item) => <option value={item.id} key={item.id}>{item.airline_code} · {item.client_safe_label || item.commercial_name || item.family_name}</option>)}</select><div className="mt-3 grid gap-2 sm:grid-cols-2">{Object.keys(emptyFare).map((key) => key === "changeability" || key === "refundability" ? <select key={key} value={manualFare[key]} onChange={(event) => setManualFare({ ...manualFare, [key]: event.target.value })} className="field"><option value="unknown">{title(key)} unknown</option><option value="included">Included</option><option value="conditional">Conditional</option><option value="not_included">Not included</option></select> : <input key={key} value={manualFare[key]} onChange={(event) => setManualFare({ ...manualFare, [key]: event.target.value })} placeholder={title(key)} className="field" />)}</div><button type="button" onClick={() => addManualFare().catch(fail(setError))} className="mt-3 secondary-button"><Plus className="h-4 w-4" />Add manual fare</button><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{selectedFares.map((fare) => <div key={fare.id} className="flex items-center justify-between gap-3 py-3"><button type="button" onClick={() => setSelectedFareId(fare.id)} className="min-w-0 text-left"><p className="truncate text-sm font-semibold text-slate-900">{fare.client_safe_label}</p><p className="mt-1 text-xs text-slate-500">{fare.source_type === "governed_fare_intelligence" ? "Governed" : "Manual"} · {fare.booking_class || "RBD unknown"} · {title(fare.uncertainty_status)}</p></button><div className="flex gap-1"><button type="button" title="Duplicate fare choice" onClick={() => duplicateFare(fare.id).catch(fail(setError))} className="icon-button"><Copy className="h-4 w-4" /></button><button type="button" title="Move fare choice up" onClick={() => moveFare(fare.id, -1).catch(fail(setError))} className="icon-button"><ArrowUp className="h-4 w-4" /></button><button type="button" title="Move fare choice down" onClick={() => moveFare(fare.id, 1).catch(fail(setError))} className="icon-button"><ArrowDown className="h-4 w-4" /></button><button type="button" title="Archive fare choice" onClick={() => archiveFare(fare.id).catch(fail(setError))} className="icon-button"><Archive className="h-4 w-4" /></button></div></div>)}</div>{archivedFares.length ? <details className="mt-3"><summary className="cursor-pointer text-sm font-semibold text-slate-700">Archived fare choices</summary>{archivedFares.map((fare) => <div key={fare.id} className="mt-2 flex items-center justify-between text-sm"><span>{fare.client_safe_label}</span><button type="button" title="Restore fare choice" onClick={() => restoreFare(fare.id).catch(fail(setError))} className="icon-button"><Undo2 className="h-4 w-4" /></button></div>)}</details> : null}</div></section> : null}

            {activeOption ? <section><div className="flex items-center gap-2"><CircleDollarSign className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Commercial values</h3></div><p className="mt-1 text-sm text-slate-600">Select a fare choice. The total is validated as base or supplier amount plus taxes, ancillaries, fees and markup, less discount.</p><div className="mt-3 grid gap-3 md:grid-cols-3"><select value={selectedFareId} onChange={(event) => setSelectedFareId(event.target.value)} className="field"><option value="">Select fare choice...</option>{selectedFares.map((item) => <option value={item.id} key={item.id}>{item.client_safe_label}</option>)}</select>{Object.keys(emptyPrice).map((key) => <input key={key} type={key.includes("until") ? "datetime-local" : key === "currency" ? "text" : "number"} step="0.01" value={price[key]} onChange={(event) => setPrice({ ...price, [key]: event.target.value })} placeholder={title(key)} className="field" />)}</div><button type="button" onClick={() => savePrice().catch(fail(setError))} className="mt-3 primary-button"><Save className="h-4 w-4" />Validate and save</button></section> : null}

            <section><div className="flex flex-wrap items-end justify-between gap-3"><div><div className="flex items-center gap-2"><GitCompareArrows className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Comparison and service review</h3></div><p className="mt-1 text-sm text-slate-600">Unknown and conditional results stay explicit. Lowest-price and shortest-duration values are deterministic hints, not guaranteed recommendations.</p></div><div className="flex gap-2"><button type="button" onClick={() => assessServices().catch(fail(setError))} className="secondary-button"><ShieldAlert className="h-4 w-4" />Assess services</button><button type="button" onClick={() => compareOptions().catch(fail(setError))} className="primary-button"><GitCompareArrows className="h-4 w-4" />Compare</button></div></div>{comparison ? <ComparisonTable comparison={comparison} /> : <p className="mt-4 border-y border-slate-200 py-4 text-sm text-slate-500">Generate a comparison after adding route and fare choices.</p>}</section>

            <section><h3 className="text-lg font-semibold text-slate-950">Offer handoff preview</h3><p className="mt-1 text-sm text-slate-600">This only links an immutable composition snapshot to an existing Offer Workspace. It does not publish, send, accept, book, ticket, issue an EMD, contact a provider, or change accepted-offer snapshots.</p><div className="mt-3 flex flex-wrap gap-2"><input value={offerId} onChange={(event) => setOfferId(event.target.value)} placeholder="Existing Offer Workspace ID" className="field max-w-lg" /><button type="button" onClick={() => previewHandoff().catch(fail(setError))} className="secondary-button">Preview handoff</button>{handoff?.can_apply ? <button type="button" onClick={() => applyHandoff().catch(fail(setError))} className="primary-button">Link snapshot</button> : null}</div>{handoff ? <pre className="mt-4 max-h-64 overflow-auto border-y border-slate-200 bg-slate-50 p-4 text-xs text-slate-700">{JSON.stringify(handoff.preview || handoff.offer_handoff, null, 2)}</pre> : null}</section>

            {(detail.options || []).some((item) => item.archived_at) ? <details><summary className="cursor-pointer font-semibold text-slate-700">Archived options</summary><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{detail.options.filter((item) => item.archived_at).map((item) => <div className="flex items-center justify-between py-3" key={item.id}><span>{item.client_safe_label}</span><button type="button" title="Restore option" onClick={() => restoreOption(item.id).catch(fail(setError))} className="icon-button"><Undo2 className="h-4 w-4" /></button></div>)}</div></details> : null}
          </main> : <EmptyState title="No composition selected" body="Open a canonical Journey and create its first option composition." />}
        </div>
      </div>
    </ProtectedRoute>
  </AgencyLayout>
}

function OptionCard({ option, detail, selected, onSelect, onClone, onMove, onArchive, onPreferred, onError }) {
  const metric = detail.metric_snapshots?.find((item) => item.id === option.metric_snapshot_id)
  const fares = detail.fare_brand_choices?.filter((item) => item.option_id === option.id && !item.archived_at) || []
  return <article className={`rounded-md border bg-white p-4 ${selected ? "border-blue-500 ring-2 ring-blue-100" : "border-slate-200"}`}><button type="button" onClick={() => onSelect(option.id)} className="block w-full text-left"><div className="flex justify-between gap-3"><div><p className="text-xs font-semibold uppercase text-blue-700">{option.option_code}</p><h4 className="mt-1 font-semibold text-slate-950">{option.client_safe_label}</h4></div><Badge value={option.status} warning={option.requires_review} /></div><p className="mt-3 text-sm font-semibold text-slate-800">{option.route_summary || "Route not composed"}</p><p className="mt-1 text-sm text-slate-600">{option.carrier_summary || "Carrier unknown"}</p><dl className="mt-4 grid grid-cols-2 gap-2 text-sm"><Info label="Duration" value={duration(metric?.total_elapsed_minutes)} /><Info label="Stops" value={metric?.stop_count ?? "Unknown"} /><Info label="Connections" value={metric?.connection_count ?? "Unknown"} /><Info label="Shortest" value={duration(metric?.shortest_connection_minutes)} /></dl></button><div className="mt-4 border-t border-slate-200 pt-3"><p className="text-xs font-semibold uppercase text-slate-500">Fare choices {fares.length}/3 target</p>{fares.map((fare) => <button type="button" onClick={() => onPreferred(option.id, fare.id).catch(fail(onError))} key={fare.id} className="mt-2 flex w-full justify-between border-b border-slate-100 py-2 text-left text-sm"><span><strong>{fare.client_safe_label}</strong><span className="ml-2 text-slate-500">{fare.cabin || "Cabin unknown"}</span></span><span className="text-slate-500">{title(fare.uncertainty_status)}</span></button>)}</div>{(option.warning_codes || []).length ? <div className="mt-3 flex flex-wrap gap-1">{option.warning_codes.slice(0, 4).map((item) => <Badge key={item} value={item} warning />)}</div> : null}<div className="mt-4 flex gap-1"><button title="Clone option" type="button" className="icon-button" onClick={() => onClone(option.id).catch(fail(onError))}><Copy className="h-4 w-4" /></button><button title="Move option left" type="button" className="icon-button" onClick={() => onMove(option.id, -1).catch(fail(onError))}><ArrowUp className="h-4 w-4" /></button><button title="Move option right" type="button" className="icon-button" onClick={() => onMove(option.id, 1).catch(fail(onError))}><ArrowDown className="h-4 w-4" /></button><button title="Archive option" type="button" className="icon-button" onClick={() => onArchive(option.id).catch(fail(onError))}><Archive className="h-4 w-4" /></button></div></article>
}

function ComparisonTable({ comparison }) {
  const rows = comparison.human_readable_rows || []
  return <div className="mt-4 overflow-x-auto border-y border-slate-200"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500"><tr><th className="px-3 py-3">Option</th><th className="px-3 py-3">Fare brand</th><th className="px-3 py-3">Price</th><th className="px-3 py-3">Journey</th><th className="px-3 py-3">Baggage</th><th className="px-3 py-3">Flexibility</th><th className="px-3 py-3">Warnings</th></tr></thead><tbody className="divide-y divide-slate-100">{rows.map((row, index) => <tr key={`${row.option}-${row.fare_brand}-${index}`}><td className="px-3 py-3 font-semibold">{row.option}</td><td className="px-3 py-3">{row.fare_brand}</td><td className="px-3 py-3">{row.price}</td><td className="px-3 py-3">{row.journey}</td><td className="px-3 py-3">{row.baggage}</td><td className="px-3 py-3">{row.flexibility}</td><td className="px-3 py-3 text-amber-800">{row.warnings?.length || 0}</td></tr>)}</tbody></table></div>
}

function Metric({ label, value, warning }) { return <div className={`rounded-md border p-4 ${warning ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-white"}`}><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div> }
function Info({ label, value }) { return <div><dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt><dd className="mt-1 font-semibold text-slate-900">{value}</dd></div> }
function Badge({ value, warning }) { return <span className={`inline-flex h-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${warning ? "bg-amber-50 text-amber-800 ring-amber-200" : "bg-blue-50 text-blue-700 ring-blue-200"}`}>{title(value)}</span> }
function clean(value) { return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== "" && item != null)) }
function cleanFare(value) { const result = clean(value); if (typeof result.client_visible_highlights === "string") result.client_visible_highlights = result.client_visible_highlights.split(",").map((item) => item.trim()).filter(Boolean); return result }
function numericPrice(value) { return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, key === "currency" || key.includes("until") ? item : Number(item)])) }
function title(value) { return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) }
function date(value) { return value ? new Date(`${String(value).slice(0, 10)}T00:00:00`).toLocaleDateString() : "Travel date unknown" }
function duration(value) { if (value == null) return "Unknown"; return `${Math.floor(value / 60)}h ${value % 60}m` }
function fail(setError) { return (error) => setError(error.message) }
