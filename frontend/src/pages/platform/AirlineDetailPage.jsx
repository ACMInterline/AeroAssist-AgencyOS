import { useEffect, useState } from "react"
import ConfidenceBadge from "../../components/ConfidenceBadge"
import EmptyState from "../../components/EmptyState"
import KnowledgeCategoryBadge from "../../components/KnowledgeCategoryBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ReviewStatusBadge from "../../components/ReviewStatusBadge"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const categories = ["booking_policy", "servicing_policy", "special_service", "baggage", "pet_travel", "accessibility", "unaccompanied_minor", "medical_travel", "documents", "contact", "payment", "refund_exchange", "schedule_change", "disruption", "emd", "fare_family", "operational_note", "other"]

export default function AirlineDetailPage({ airlineId }) {
  const [state, setState] = useState(null)
  const [knowledge, setKnowledge] = useState({ category: "special_service", title: "", summary: "", detailed_text: "", service_code: "", confidence: "medium", review_status: "draft", tags: "" })
  const [procedure, setProcedure] = useState({ procedure_type: "special_service_request", title: "", channel: "gds", contact_value: "", instructions: "", required_fields: "" })
  const [emd, setEmd] = useState({ service_code: "", service_name: "", rfic_code: "", rfisc_code: "", emd_type: "unknown", reason_for_issuance: "", applies_to: "other" })
  const [source, setSource] = useState({ source_type: "airline_website", title: "", url: "", reliability: "official", notes: "" })
  const [error, setError] = useState("")

  async function load() {
    const [summary, detail] = await Promise.all([apiGet("/api/platform/summary"), apiGet(`/api/platform/airlines/${airlineId}`)])
    setState({ summary, ...detail })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [airlineId])

  function update(setter, name, value) {
    setter((current) => ({ ...current, [name]: value }))
  }

  async function createKnowledge(event) {
    event.preventDefault()
    await apiPost(`/api/platform/airlines/${airlineId}/knowledge`, {
      ...knowledge,
      service_code: knowledge.service_code || null,
      tags: knowledge.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
      source_ids: [],
    })
    setKnowledge({ category: "special_service", title: "", summary: "", detailed_text: "", service_code: "", confidence: "medium", review_status: "draft", tags: "" })
    await load()
  }

  async function createProcedure(event) {
    event.preventDefault()
    await apiPost(`/api/platform/airlines/${airlineId}/procedures`, {
      ...procedure,
      contact_value: procedure.contact_value || null,
      required_fields: procedure.required_fields.split(",").map((field) => field.trim()).filter(Boolean),
      review_status: "published",
      confidence: "medium",
      source_ids: [],
    })
    setProcedure({ procedure_type: "special_service_request", title: "", channel: "gds", contact_value: "", instructions: "", required_fields: "" })
    await load()
  }

  async function createEmd(event) {
    event.preventDefault()
    await apiPost(`/api/platform/airlines/${airlineId}/emd-notes`, { ...emd, rfic_code: emd.rfic_code || null, rfisc_code: emd.rfisc_code || null, review_status: "published", confidence: "medium", source_ids: [] })
    setEmd({ service_code: "", service_name: "", rfic_code: "", rfisc_code: "", emd_type: "unknown", reason_for_issuance: "", applies_to: "other" })
    await load()
  }

  async function createSource(event) {
    event.preventDefault()
    await apiPost("/api/platform/airline-sources", { ...source, airline_id: airlineId, url: source.url || null })
    setSource({ source_type: "airline_website", title: "", url: "", reliability: "official", notes: "" })
    await load()
  }

  async function publishKnowledge(id) {
    await apiPost(`/api/platform/airline-knowledge/${id}/publish`)
    await load()
  }

  async function archiveKnowledge(id) {
    await apiPost(`/api/platform/airline-knowledge/${id}/archive`)
    await load()
  }

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/platform/airlines">Back to airlines</a>
            <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.airline.airline_code}</p>
            <h2 className="text-2xl font-semibold text-slate-950">{state.airline.airline_name}</h2>
            <p className="mt-1 text-sm text-slate-600">{state.airline.country} · {state.airline.notes || "No profile notes."}</p>
          </div>
          <Panel title="Create Knowledge Item">
            <form className="grid gap-3" onSubmit={createKnowledge}>
              <div className="grid gap-3 md:grid-cols-[1fr_140px_140px_140px]">
                <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Title" value={knowledge.title} onChange={(event) => update(setKnowledge, "title", event.target.value)} />
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={knowledge.category} onChange={(event) => update(setKnowledge, "category", event.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select>
                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Service code" value={knowledge.service_code} onChange={(event) => update(setKnowledge, "service_code", event.target.value.toUpperCase())} />
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={knowledge.review_status} onChange={(event) => update(setKnowledge, "review_status", event.target.value)}>{["draft", "needs_review", "verified", "published"].map((item) => <option key={item}>{item}</option>)}</select>
              </div>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Summary" value={knowledge.summary} onChange={(event) => update(setKnowledge, "summary", event.target.value)} />
              <textarea required className="min-h-28 rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Detailed text" value={knowledge.detailed_text} onChange={(event) => update(setKnowledge, "detailed_text", event.target.value)} />
              <div className="grid gap-3 md:grid-cols-[1fr_160px_auto]">
                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Tags, comma separated" value={knowledge.tags} onChange={(event) => update(setKnowledge, "tags", event.target.value)} />
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={knowledge.confidence} onChange={(event) => update(setKnowledge, "confidence", event.target.value)}>{["low", "medium", "high", "official_source"].map((item) => <option key={item}>{item}</option>)}</select>
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Create knowledge</button>
              </div>
            </form>
          </Panel>
          <Panel title="Knowledge Items">
            <List items={state.knowledge} empty="No knowledge items yet" render={(item) => (
              <div className="flex flex-wrap items-start justify-between gap-3">
                <a className="min-w-0 text-blue-700" href={`/platform/airline-knowledge/${item.id}`}>{item.title}</a>
                <div className="flex flex-wrap gap-2"><KnowledgeCategoryBadge category={item.category} /><ReviewStatusBadge status={item.review_status} /><ConfidenceBadge confidence={item.confidence} /></div>
                <div className="flex gap-2">
                  <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" onClick={() => publishKnowledge(item.id)}>Publish</button>
                  <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" onClick={() => archiveKnowledge(item.id)}>Archive</button>
                </div>
              </div>
            )} />
          </Panel>
          <section className="grid gap-4 lg:grid-cols-3">
            <Panel title="Create Procedure">
              <form className="space-y-3" onSubmit={createProcedure}>
                <input required className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Title" value={procedure.title} onChange={(event) => update(setProcedure, "title", event.target.value)} />
                <select className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={procedure.procedure_type} onChange={(event) => update(setProcedure, "procedure_type", event.target.value)}>{["reservation", "ticketing", "reissue", "refund", "emd", "special_service_request", "pet_booking", "wheelchair_assistance", "umnr", "medical_clearance", "group_booking", "disruption", "agency_support", "other"].map((item) => <option key={item}>{item}</option>)}</select>
                <select className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={procedure.channel} onChange={(event) => update(setProcedure, "channel", event.target.value)}>{["gds", "airline_portal", "email", "phone", "webform", "sales_office", "airport", "other"].map((item) => <option key={item}>{item}</option>)}</select>
                <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Contact value" value={procedure.contact_value} onChange={(event) => update(setProcedure, "contact_value", event.target.value)} />
                <textarea required className="min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Instructions" value={procedure.instructions} onChange={(event) => update(setProcedure, "instructions", event.target.value)} />
                <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Required fields" value={procedure.required_fields} onChange={(event) => update(setProcedure, "required_fields", event.target.value)} />
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Create</button>
              </form>
            </Panel>
            <Panel title="Create EMD Note">
              <form className="space-y-3" onSubmit={createEmd}>
                <input required className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Service code" value={emd.service_code} onChange={(event) => update(setEmd, "service_code", event.target.value.toUpperCase())} />
                <input required className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Service name" value={emd.service_name} onChange={(event) => update(setEmd, "service_name", event.target.value)} />
                <div className="grid grid-cols-2 gap-2"><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="RFIC" value={emd.rfic_code} onChange={(event) => update(setEmd, "rfic_code", event.target.value)} /><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="RFISC" value={emd.rfisc_code} onChange={(event) => update(setEmd, "rfisc_code", event.target.value)} /></div>
                <select className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={emd.applies_to} onChange={(event) => update(setEmd, "applies_to", event.target.value)}>{["petc", "avih", "wchr", "wchs", "wchc", "umnr", "baggage", "seat", "meal", "medical", "other"].map((item) => <option key={item}>{item}</option>)}</select>
                <textarea required className="min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Reason for issuance" value={emd.reason_for_issuance} onChange={(event) => update(setEmd, "reason_for_issuance", event.target.value)} />
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Create</button>
              </form>
            </Panel>
            <Panel title="Create Source">
              <form className="space-y-3" onSubmit={createSource}>
                <input required className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Title" value={source.title} onChange={(event) => update(setSource, "title", event.target.value)} />
                <select className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={source.source_type} onChange={(event) => update(setSource, "source_type", event.target.value)}>{["airline_website", "airline_pdf", "gds_entry", "email_from_airline", "phone_note", "agency_experience", "atpco_iata_reference", "internal_note", "other"].map((item) => <option key={item}>{item}</option>)}</select>
                <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="URL" value={source.url} onChange={(event) => update(setSource, "url", event.target.value)} />
                <textarea className="min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Notes" value={source.notes} onChange={(event) => update(setSource, "notes", event.target.value)} />
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Create</button>
              </form>
            </Panel>
          </section>
          <section className="grid gap-4 lg:grid-cols-3">
            <Panel title="Procedures"><List items={state.procedures} empty="No procedures yet" render={(item) => `${item.title} · ${item.channel.replaceAll("_", " ")} · ${item.procedure_type.replaceAll("_", " ")}`} /></Panel>
            <Panel title="EMD Notes"><List items={state.emd_notes} empty="No EMD notes yet" render={(item) => `${item.service_code} · ${item.service_name} · ${item.emd_type.replaceAll("_", " ")}`} /></Panel>
            <Panel title="Sources"><List items={state.sources} empty="No sources yet" render={(item) => `${item.title} · ${item.source_type.replaceAll("_", " ")} · ${item.reliability}`} /></Panel>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function List({ items, empty, render }) {
  if (!items?.length) return <EmptyState title={empty} body="Add platform-maintained records when source evidence is ready." />
  return <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>)}</div>
}
