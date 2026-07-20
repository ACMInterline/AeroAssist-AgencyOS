import { useEffect, useMemo, useState } from "react"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import Columns3 from "lucide-react/dist/esm/icons/columns-3.js"
import Copy from "lucide-react/dist/esm/icons/copy.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import Wand2 from "lucide-react/dist/esm/icons/wand-2.js"
import OfferDeliveryPanel from "../../components/offers/OfferDeliveryPanel"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function OfferWorkspaceDetailPage({ workspaceId }) {
  const query = useMemo(() => new URLSearchParams(window.location.search), [workspaceId])
  const section = query.get("section") || "overview"
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ label: "New option", option_type: "flight", main_airline_code: "", provider_name: "manual" })
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load() {
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
    setState({ ...context, ...detail, matrix: comparison.matrix, acceptance, bookingWorkspaces: bookingWorkspaces.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [workspaceId])

  const childCounts = useMemo(() => {
    const optionIds = new Set((state?.options || []).map((option) => option.id))
    return {
      options: optionIds.size,
      segments: (state?.segments || []).length,
      fareBundles: (state?.fare_bundles || []).length,
      pricingLines: (state?.pricing_lines || []).length,
      warnings: (state?.options || []).reduce((sum, option) => sum + (option.warnings_json?.length || 0), 0),
    }
  }, [state])
  const accepted = state?.acceptance?.acceptance
  const readiness = state?.acceptance?.booking_readiness
  const bookingWorkspace = state?.bookingWorkspaces?.[0]

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function addOption(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/offer-workspaces/${workspaceId}/options`, {
        label: form.label || "New option",
        option_type: form.option_type,
        main_airline_code: form.main_airline_code || null,
        provider_name: form.provider_name,
      })
      setForm({ label: "New option", option_type: "flight", main_airline_code: "", provider_name: "manual" })
      setMessage("Option added.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function cloneOption(optionId) {
    await apiPost(`/api/agencies/${state.agency.id}/offer-options/${optionId}/clone`)
    await load()
  }

  async function recommendOption(optionId) {
    await apiPost(`/api/agencies/${state.agency.id}/offer-workspaces/${workspaceId}/recommend`, { option_id: optionId, tag: "Recommended", rank: 1 })
    await load()
  }

  async function acceptOption(optionId) {
    setError("")
    setMessage("")
    try {
      await apiPost(
        `/api/agencies/${state.agency.id}/offer-workspaces/${workspaceId}/options/${optionId}/accept`,
        {
          acceptance_source: "internal",
          provider_target: "manual",
        },
      )
      setMessage("Offer option accepted. Trip snapshot and booking readiness were refreshed.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function saveSnapshot() {
    await apiPost(`/api/agencies/${state.agency.id}/offer-workspaces/${workspaceId}/comparison/snapshot`)
    setMessage("Comparison snapshot saved.")
    await load()
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <a className="text-sm font-medium text-blue-700" href="/agency/offers">Back to offers</a>
                <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state?.workspace?.status?.replaceAll("_", " ")} · {state?.workspace?.currency}</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">{state?.workspace?.title}</h2>
                <p className="mt-1 text-sm text-slate-600">{contextLabel(state)}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <a className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={documentHref("offer_summary", "offer_workspace", workspaceId)}>
                  Documents
                </a>
                <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={saveSnapshot}>
                  <Copy className="h-4 w-4" />
                  Snapshot
                </button>
                <a className="aa-primary-action inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/offers/${workspaceId}/builder`}>
                  <Wand2 className="h-4 w-4" />
                  Builder
                </a>
              </div>
            </div>
          </div>

          <WorkflowContinuityPanel
            breadcrumbs={[{ label: "Trips", href: state?.trip?.id ? `/agency/trips/${state.trip.id}` : "/agency/trips" }, { label: "Offers", href: "/agency/offers" }]}
            currentLabel={state?.workspace?.title || "Offer"}
            status={accepted ? "accepted" : state?.workspace?.status}
            validation={accepted && readiness ? { state: "ready", label: "Accepted snapshot ready", reason: "Continue through the canonical booking handoff." } : { state: state?.options?.length ? "warning" : "blocked", label: state?.options?.length ? "Acceptance pending" : "Option required", reason: state?.options?.length ? "Accept one reviewed option before booking." : "Build an offer option first." }}
            previous={state?.trip?.id ? { label: "Previous: trip", href: `/agency/trips/${state.trip.id}` } : { label: "Offers", href: "/agency/offers" }}
            next={bookingWorkspace
              ? { label: "Continue to booking", href: `/agency/booking-workspaces/${bookingWorkspace.id}` }
              : { label: "Continue to handoff", href: accepted && readiness ? `/agency/booking-handoffs?acceptance_id=${encodeURIComponent(accepted.id)}&booking_readiness_package_id=${encodeURIComponent(readiness.id)}&trip_id=${encodeURIComponent(accepted.trip_id || state?.trip?.id || "")}&offer_workspace_id=${encodeURIComponent(workspaceId)}` : undefined, enabled: Boolean(accepted && readiness), reason: "Accepted snapshot and readiness are required." }}
            relatedRecords={[{ label: "Trip", value: state?.trip?.trip_reference || "none", href: state?.trip?.id ? `/agency/trips/${state.trip.id}` : undefined }, { label: "Options", value: state?.options?.length || 0 }, { label: "Readiness", value: readiness?.status || "not created" }]}
          />

          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div> : null}

          <OfferLifecycleNavigation workspaceId={workspaceId} active={section} />

          {section === "delivery" ? <OfferDeliveryPanel agency={state?.agency} offerId={workspaceId} clientId={state?.workspace?.client_summary_json?.client_id || ""} presentationId={query.get("presentation_id") || ""} showHeader={false} /> : section === "client" ? <ClientPassengerContext state={state} /> : section === "suitability" ? <AirlineSuitability options={state?.options || []} /> : section === "history" ? <OfferHistory state={state} /> : <>
          <AcceptancePanel state={state} />

          <section className="grid gap-4 md:grid-cols-5">
            <Metric label="Options" value={childCounts.options} />
            <Metric label="Segments" value={childCounts.segments} />
            <Metric label="Fare Bundles" value={childCounts.fareBundles} />
            <Metric label="Price Lines" value={childCounts.pricingLines} />
            <Metric label="Warnings" value={childCounts.warnings} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addOption}>
              <h3 className="font-semibold text-slate-950">Add Option</h3>
              <Field label="Label"><input value={form.label} onChange={(event) => setField("label", event.target.value)} /></Field>
              <Field label="Type">
                <select value={form.option_type} onChange={(event) => setField("option_type", event.target.value)}>
                  {["flight", "package", "service_only", "manual"].map((value) => <option value={value} key={value}>{value.replaceAll("_", " ")}</option>)}
                </select>
              </Field>
              <Field label="Main Airline">
                <input value={form.main_airline_code} onChange={(event) => setField("main_airline_code", event.target.value.toUpperCase())} maxLength={3} />
              </Field>
              <Field label="Provider">
                <select value={form.provider_name} onChange={(event) => setField("provider_name", event.target.value)}>
                  {["manual", "travelport", "amadeus", "ndc", "supplier", "other"].map((value) => <option value={value} key={value}>{value}</option>)}
                </select>
              </Field>
              <button className="aa-primary-action inline-flex w-full items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-semibold" type="submit">
                <Plus className="h-4 w-4" />
                Add Option
              </button>
            </form>

            <div className="space-y-4">
              {(state?.options || []).length ? (
                <div className="grid gap-4 lg:grid-cols-2">
                  {state.options.map((option) => (
                    <OptionCard
                      option={option}
                      key={option.id}
                      acceptedOptionId={state.acceptance?.acceptance?.option_id}
                      onAccept={() => acceptOption(option.id)}
                      onClone={() => cloneOption(option.id)}
                      onRecommend={() => recommendOption(option.id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8">
                  <EmptyState title="No options yet" body="Add the first option to begin comparison." />
                </div>
              )}
            </div>
          </section>

          <ComparisonMatrix matrix={state?.matrix} />
          </>}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function OfferLifecycleNavigation({ workspaceId, active }) {
  const encoded = encodeURIComponent(workspaceId)
  const stages = [
    ["overview", "Overview", `/agency/offers/${encoded}`],
    ["client", "Client & Passengers", `/agency/offers/${encoded}?section=client`],
    ["itinerary", "Itinerary Builder", `/agency/journey-authoring?offer_id=${encoded}`],
    ["options", "Itinerary Options & Fare Brands", `/agency/journey-option-composition?offer_id=${encoded}`],
    ["suitability", "Airline Suitability", `/agency/offers/${encoded}?section=suitability`],
    ["comparison", "Offer Comparison", `/agency/journey-comparison-presentations?offer_id=${encoded}`],
    ["preview", "Client Preview", `/agency/journey-comparison-presentations?offer_id=${encoded}&view=client-preview`],
    ["delivery", "Delivery & Responses", `/agency/offers/${encoded}?section=delivery`],
    ["history", "History", `/agency/offers/${encoded}?section=history`],
  ]
  return <nav className="flex gap-1 overflow-x-auto border-y border-slate-200 py-3" aria-label="Offer lifecycle">{stages.map(([key, label, href]) => <a className={`whitespace-nowrap rounded-md px-3 py-2 text-sm font-semibold ${active === key ? "bg-blue-700 text-white" : "text-slate-700 hover:bg-slate-100"}`} href={href} key={key}>{label}</a>)}</nav>
}

function ClientPassengerContext({ state }) {
  const summary = state?.workspace?.client_summary_json || {}
  return <section className="space-y-5"><div><h3 className="text-lg font-semibold text-slate-950">Client & Passengers</h3><p className="mt-1 text-sm text-slate-600">This Offer references canonical Client and Passenger records; profiles remain owned by their respective workspaces.</p></div><dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><ContextValue label="Client" value={summary.client_name || summary.client_id} /><ContextValue label="Passengers" value={summary.passenger_names?.join(", ") || summary.passenger_count} /><ContextValue label="Request" value={state?.request?.request_reference} /><ContextValue label="Trip" value={state?.trip?.trip_reference} /></dl><div className="flex flex-wrap gap-2"><a className="secondary-button" href="/agency/clients">Open Clients</a><a className="secondary-button" href="/agency/passengers">Open Passengers</a></div></section>
}

function AirlineSuitability({ options }) {
  return <section><h3 className="text-lg font-semibold text-slate-950">Airline Suitability</h3><p className="mt-1 text-sm text-slate-600">Advisory service suitability remains separate from confirmed airline approval.</p><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{options.map((option) => <div className="grid gap-2 py-4 md:grid-cols-[minmax(0,1fr)_180px_140px]" key={option.id}><div><p className="font-semibold text-slate-950">{option.label}</p><p className="mt-1 text-sm text-slate-600">{option.service_feasibility_json?.client_summary || "Service suitability requires agent review."}</p></div><span className="text-sm">{String(option.service_feasibility_json?.overall_status || "unknown").replaceAll("_", " ")}</span><span className="text-sm text-slate-500">{option.main_airline_code || "Airline unknown"}</span></div>)}</div>{!options.length ? <EmptyState title="No itinerary options" body="Prepare itinerary options before assessing airline suitability." /> : null}</section>
}

function OfferHistory({ state }) {
  const history = state?.acceptance?.history || []
  return <section><h3 className="text-lg font-semibold text-slate-950">Offer History</h3><p className="mt-1 text-sm text-slate-600">Acceptance history is shown here; delivery views and client responses remain available under Delivery & Responses.</p>{history.length ? <div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{history.map((item) => <div className="py-3 text-sm" key={item.id}><p className="font-semibold text-slate-950">{String(item.status || "recorded").replaceAll("_", " ")}</p><p className="mt-1 text-slate-600">{item.client_visible_summary_json?.option_label || item.option_id}</p><p className="mt-1 text-xs text-slate-500">{String(item.updated_at || item.created_at || "").slice(0, 19)}</p></div>)}</div> : <EmptyState title="No history yet" body="Offer acceptance and response history will appear here." />}</section>
}

function ContextValue({ label, value }) { return <div className="border-y border-slate-200 py-3"><dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt><dd className="mt-1 text-sm font-semibold text-slate-950">{value || "Not linked"}</dd></div> }

function contextLabel(state) {
  const request = state?.request
  const trip = state?.trip
  const parts = []
  if (request) parts.push(`${request.request_reference} - ${request.title}`)
  if (trip) parts.push(`${trip.trip_reference} - ${trip.trip_title}`)
  return parts.length ? parts.join(" | ") : "Manual workspace"
}

function AcceptancePanel({ state }) {
  const acceptance = state?.acceptance?.acceptance
  const readiness = state?.acceptance?.booking_readiness
  const history = state?.acceptance?.history || []
  const bookingWorkspace = state?.bookingWorkspaces?.[0]
  const superseded = history.filter((item) => item.status === "superseded").length
  if (!acceptance) {
    return (
      <section className="rounded-lg border border-dashed border-slate-300 bg-white p-5">
        <h3 className="font-semibold text-slate-950">Acceptance</h3>
        <p className="mt-2 text-sm text-slate-500">No offer option has been accepted for this workspace yet.</p>
      </section>
    )
  }
  return (
    <section className="rounded-lg border border-emerald-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">{acceptance.status}</p>
          <h3 className="mt-1 font-semibold text-slate-950">Accepted Offer</h3>
          <p className="mt-1 text-sm text-slate-600">{acceptance.client_visible_summary_json?.option_label || acceptance.option_id}</p>
          {superseded ? (
            <p className="mt-2 text-sm text-amber-700">
              {superseded} previous acceptance was superseded for this workspace.
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          {acceptance.trip_id ? (
            <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/trips/${acceptance.trip_id}`}>
              Open trip
            </a>
          ) : null}
          {readiness ? (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
              Readiness: {readiness.status}
            </span>
          ) : null}
          {readiness ? (
            <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/booking-handoffs?acceptance_id=${acceptance.id}&booking_readiness_package_id=${readiness.id}&trip_id=${acceptance.trip_id || ""}&offer_workspace_id=${state?.workspace?.id || ""}`}>
              Review booking handoff
            </a>
          ) : null}
          <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={documentHref("offer_comparison", "offer_workspace", state?.workspace?.id)}>
            Offer documents
          </a>
          {bookingWorkspace ? (
            <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/booking-workspaces/${bookingWorkspace.id}`}>
              Open booking workspace
            </a>
          ) : readiness ? (
            <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/booking-handoffs?acceptance_id=${acceptance.id}&booking_readiness_package_id=${readiness.id}&trip_id=${acceptance.trip_id || ""}&offer_workspace_id=${state?.workspace?.id || ""}`}>
              Continue to booking handoff
            </a>
          ) : null}
        </div>
      </div>
    </section>
  )
}

function OptionCard({ option, acceptedOptionId, onAccept, onClone, onRecommend }) {
  const pricing = option.pricing_summary_json || {}
  const warnings = option.warnings_json || []
  const accepted = option.id === acceptedOptionId
  return (
    <article
      className={`rounded-lg border bg-white p-5 ${accepted ? "border-emerald-300" : "border-slate-200"}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {accepted ? "accepted" : option.status?.replaceAll("_", " ")} · {option.provider_name}
          </p>
          <h3 className="mt-1 font-semibold text-slate-950">{option.label}</h3>
          <p className="mt-1 text-sm text-slate-600">{option.main_airline_code || "Airline pending"} · {option.option_type?.replaceAll("_", " ")}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{money(pricing.total_amount, pricing.currency)}</span>
      </div>
      <div className="mt-4 grid gap-2 text-sm text-slate-600 md:grid-cols-3">
        <span>Rules: {(option.rules_summary_json?.status || "pending").replaceAll("_", " ")}</span>
        <span>Services: {(option.service_feasibility_json?.overall_status || "pending").replaceAll("_", " ")}</span>
        <span>Warnings: {warnings.length}</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <a className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" href={`/agency/offers/${option.workspace_id}/builder?option=${option.id}`}>Open</a>
        <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onClone}>
          <Copy className="h-4 w-4" />
          Clone
        </button>
        <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onRecommend}>
          <CheckCircle2 className="h-4 w-4" />
          Recommend
        </button>
        <button
          className="aa-primary-action inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold"
          type="button"
          onClick={onAccept}
          disabled={accepted}
        >
          <CheckCircle2 className="h-4 w-4" />
          {accepted ? "Accepted" : "Accept"}
        </button>
      </div>
    </article>
  )
}

function ComparisonMatrix({ matrix }) {
  if (!matrix?.columns?.length) {
    return (
      <section className="rounded-lg border border-dashed border-slate-300 bg-white p-8">
        <EmptyState title="Comparison matrix is empty" body="Add options to generate internal comparison rows." />
      </section>
    )
  }
  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-4">
        <Columns3 className="h-4 w-4 text-blue-700" />
        <h3 className="font-semibold text-slate-950">Internal Comparison Matrix</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
              <th className="w-56 px-4 py-3">Row</th>
              {matrix.columns.map((column) => <th className="min-w-48 px-4 py-3" key={column.option_id}>{column.label}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {matrix.rows.map((row) => (
              <tr key={row.key} className={row.severity ? "bg-amber-50/60" : ""}>
                <th className="px-4 py-3 font-semibold text-slate-800">{row.label}</th>
                {matrix.columns.map((column) => <td className="px-4 py-3 text-slate-700" key={`${row.key}-${column.option_id}`}>{displayValue(row.values?.[column.option_id])}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
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

function money(amount, currency) {
  if (amount === null || amount === undefined || amount === "") return "Not priced"
  return `${Number(amount).toFixed(2)} ${currency || "EUR"}`
}

function displayValue(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  if (typeof value === "boolean") return value ? "Yes" : "No"
  return String(value)
}

function documentHref(documentType, sourceContextType, sourceContextId) {
  const params = new URLSearchParams({
    document_type: documentType,
    source_context_type: sourceContextType,
    source_context_id: sourceContextId || "",
  })
  return `/agency/documents?${params.toString()}`
}
