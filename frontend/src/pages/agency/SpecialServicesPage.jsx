import { cloneElement, useEffect, useMemo, useState } from "react"
import FileText from "lucide-react/dist/esm/icons/file-text.js"
import Play from "lucide-react/dist/esm/icons/play.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import Wand2 from "lucide-react/dist/esm/icons/wand-2.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const serviceTypes = ["UMNR", "WCHR", "WCHS", "WCHC", "WCHP", "WCHD", "BLND", "DEAF", "MEDA", "MEDIF", "OXYG", "STCR", "PETC", "AVIH", "SVAN", "EXST", "SPML", "SPEQ", "WEAP", "DIPB", "VIP", "VVIP"]

const emptyForm = {
  category: "PRM",
  service_type: "WCHR",
  passenger_id: "",
  segment_id: "",
  metadata_json: "{}",
}

function categoryForServiceType(serviceType) {
  if (serviceType === "UMNR") return "UMNR"
  if (["WCHR", "WCHS", "WCHC", "WCHP", "WCHD", "BLND", "DEAF"].includes(serviceType)) return "PRM"
  if (["MEDA", "MEDIF", "OXYG", "STCR"].includes(serviceType)) return "MEDICAL"
  if (["PETC", "AVIH"].includes(serviceType)) return "PETS"
  if (serviceType === "SVAN") return "SERVICE_ANIMAL"
  if (["SPEQ", "WEAP"].includes(serviceType)) return "CARGO"
  if (["VIP", "VVIP", "DIPB"].includes(serviceType)) return "VIP"
  if (serviceType === "EXST") return "SEATING"
  if (serviceType === "SPML") return "MEAL"
  return "OTHER"
}

export default function SpecialServicesPage({ requestId, tripId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const mode = requestId ? "request" : "trip"

  async function load() {
    const context = await loadCurrentAgency()
    const agencyId = context.agency.id
    const specialServicesPath = requestId
      ? `/api/agencies/${agencyId}/requests/${requestId}/special-services`
      : `/api/agencies/${agencyId}/trips/${tripId}/special-services`
    const detailPath = requestId
      ? `/api/agencies/${agencyId}/requests/${requestId}`
      : `/api/agencies/${agencyId}/trips/${tripId}`
    const [specialServices, detail] = await Promise.all([apiGet(specialServicesPath), apiGet(detailPath)])
    setState({ ...context, specialServices, detail, items: specialServices.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [requestId, tripId])

  const passengers = state?.detail?.passengers || []
  const segments = state?.detail?.segments || []
  const grouped = useMemo(() => {
    const groups = {}
    ;(state?.items || []).forEach((item) => {
      const category = item.category || "OTHER"
      groups[category] = [...(groups[category] || []), item]
    })
    return groups
  }, [state])
  const blockedCount = (state?.items || []).filter((item) => item.status === "blocked").length
  const docCount = (state?.items || []).reduce((count, item) => count + (item.required_documents_json?.length || 0), 0)

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  function parseJson(value) {
    const trimmed = String(value || "").trim()
    if (!trimmed) return {}
    return JSON.parse(trimmed)
  }

  async function addService(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const agencyId = state.agency.id
      const path = requestId
        ? `/api/agencies/${agencyId}/requests/${requestId}/special-services`
        : `/api/agencies/${agencyId}/trips/${tripId}/special-services`
      await apiPost(path, {
        category: form.category,
        service_type: form.service_type,
        passenger_id: form.passenger_id || null,
        segment_id: form.segment_id || null,
        metadata_json: parseJson(form.metadata_json),
      })
      setForm(emptyForm)
      setMessage("Special service added.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function evaluate(item) {
    await apiPost(`/api/agencies/${state.agency.id}/special-services/${item.id}/evaluate`)
    await load()
  }

  async function generate(item) {
    await apiPost(`/api/agencies/${state.agency.id}/special-services/${item.id}/generate-ssr-osi`)
    await load()
  }

  async function generateTrip() {
    if (!tripId) return
    await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/generate-ssr-osi`)
    await load()
  }

  function updateServiceType(value) {
    setForm((current) => ({ ...current, service_type: value, category: categoryForServiceType(value) }))
  }

  const title = requestId ? state?.detail?.request?.title : state?.detail?.trip?.trip_title
  const backHref = requestId ? `/agency/requests/${requestId}` : `/agency/trips/${tripId}`

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <a className="text-sm font-medium text-blue-700" href={backHref}>Back to {mode}</a>
                <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Special Services</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">{title}</h2>
                <p className="mt-1 text-sm text-slate-600">Evaluate passenger services against platform airline rules and preview SSR/OSI text.</p>
              </div>
              {tripId ? <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="button" onClick={generateTrip}><Wand2 className="h-4 w-4" />Generate Trip SSR/OSI</button> : null}
            </div>
          </div>

          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-4 md:grid-cols-3">
            <Metric label="Services" value={state?.items?.length || 0} />
            <Metric label="Blocked" value={blockedCount} />
            <Metric label="Documents" value={docCount} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addService}>
              <h3 className="font-semibold text-slate-950">Add Service</h3>
              <Field label="Service Type"><select value={form.service_type} onChange={(event) => updateServiceType(event.target.value)}>{serviceTypes.map((value) => <option value={value} key={value}>{value}</option>)}</select></Field>
              <Field label="Category"><select value={form.category} onChange={(event) => setField("category", event.target.value)}>{["UMNR", "PRM", "MEDICAL", "PETS", "SERVICE_ANIMAL", "CARGO", "VIP", "SEATING", "MEAL", "OTHER"].map((value) => <option value={value} key={value}>{value}</option>)}</select></Field>
              <Field label="Passenger"><select value={form.passenger_id} onChange={(event) => setField("passenger_id", event.target.value)}><option value="">Any passenger</option>{passengers.map((passenger) => <option value={passenger.id} key={passenger.id}>{passenger.snapshot_display_name || passenger.display_name}</option>)}</select></Field>
              <Field label="Segment"><select value={form.segment_id} onChange={(event) => setField("segment_id", event.target.value)}><option value="">Any segment</option>{segments.map((segment) => <option value={segment.id} key={segment.id}>{segment.origin_text || segment.origin_airport_code} to {segment.destination_text || segment.destination_airport_code}</option>)}</select></Field>
              <label className="grid gap-1 text-sm font-medium text-slate-700">Metadata JSON
                <textarea className="min-h-32 rounded-md border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-xs font-normal" value={form.metadata_json} onChange={(event) => setField("metadata_json", event.target.value)} spellCheck="false" />
              </label>
              <button className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit"><Plus className="h-4 w-4" />Add Service</button>
            </form>

            <div className="space-y-4">
              {Object.keys(grouped).length ? Object.entries(grouped).map(([category, items]) => (
                <section className="rounded-lg border border-slate-200 bg-white p-5" key={category}>
                  <h3 className="font-semibold text-slate-950">{category}</h3>
                  <div className="mt-4 space-y-3">
                    {items.map((item) => <ServiceCard item={item} passengers={passengers} segments={segments} onEvaluate={() => evaluate(item)} onGenerate={() => generate(item)} key={item.id} />)}
                  </div>
                </section>
              )) : <section className="rounded-lg border border-slate-200 bg-white p-5"><EmptyState title="No special services" body="Add a service to evaluate policy, warnings, required documents, and SSR/OSI text." /></section>}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function Field({ label, children }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}{cloneElement(children, { className: `${children.props.className || ""} rounded-md border border-slate-300 px-3 py-2 text-sm font-normal` })}</label>
}

function ServiceCard({ item, passengers, segments, onEvaluate, onGenerate }) {
  const passenger = passengers.find((entry) => entry.id === item.passenger_id)
  const segment = segments.find((entry) => entry.id === item.segment_id)
  const warnings = (item.warnings_json || []).map((warning) => warning.message || JSON.stringify(warning))
  const docs = (item.required_documents_json || []).map((doc) => doc.label || doc.code || JSON.stringify(doc))
  return (
    <article className="rounded-md border border-slate-200 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-950">{item.service_type} · {item.status?.replaceAll("_", " ")}</p>
          <p className="mt-1 text-sm text-slate-600">{passenger?.snapshot_display_name || passenger?.display_name || "Any passenger"} · {segment ? `${segment.origin_text || segment.origin_airport_code} to ${segment.destination_text || segment.destination_airport_code}` : "Any segment"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onEvaluate}><Play className="h-4 w-4" />Evaluate</button>
          <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="button" onClick={onGenerate}><FileText className="h-4 w-4" />SSR/OSI</button>
        </div>
      </div>
      <section className="mt-4 grid gap-4 lg:grid-cols-2">
        <InfoList title="Warnings" items={warnings} empty="None" />
        <InfoList title="Required Documents" items={docs} empty="None" />
      </section>
      {(item.generated_ssr_json?.length || item.generated_osi_json?.length) ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          <Preview title="SSR Preview" value={item.generated_ssr_json} />
          <Preview title="OSI Preview" value={item.generated_osi_json} />
        </div>
      ) : null}
    </article>
  )
}

function InfoList({ title, items, empty }) {
  return <div><h4 className="text-sm font-semibold text-slate-950">{title}</h4>{items.length ? <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">{items.map((item, index) => <li key={`${title}-${index}`}>{item}</li>)}</ul> : <p className="mt-2 text-sm text-slate-500">{empty}</p>}</div>
}

function Preview({ title, value }) {
  return <div><h4 className="text-sm font-semibold text-slate-950">{title}</h4><pre className="mt-2 max-h-48 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(value || [], null, 2)}</pre></div>
}
