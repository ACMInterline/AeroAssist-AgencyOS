import { useEffect, useState } from "react"
import ConfidenceBadge from "../../components/ConfidenceBadge"
import EmptyState from "../../components/EmptyState"
import KnowledgeCategoryBadge from "../../components/KnowledgeCategoryBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ReviewStatusBadge from "../../components/ReviewStatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AirlineIntelligenceDetailPage({ airlineId }) {
  const [state, setState] = useState(null)
  const [override, setOverride] = useState({ target_type: "airline_profile", target_id: "", override_mode: "annotate", title: "", override_text: "", internal_warning: false })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/airlines/${airlineId}/intelligence`)
    setState({ ...context, ...detail })
    setOverride((current) => ({ ...current, target_id: detail.airline.id }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [airlineId])

  async function createOverride(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/airlines/${airlineId}/overrides`, override)
    setOverride({ target_type: "airline_profile", target_id: state.airline.id, override_mode: "annotate", title: "", override_text: "", internal_warning: false })
    await load()
  }

  const targetOptions = [
    { type: "airline_profile", id: state?.airline?.id, label: "Airline profile" },
    ...(state?.knowledge || []).map((item) => ({ type: "knowledge_item", id: item.id, label: `Knowledge: ${item.title}` })),
    ...(state?.procedures || []).map((item) => ({ type: "procedure", id: item.id, label: `Procedure: ${item.title}` })),
    ...(state?.emd_notes || []).map((item) => ({ type: "emd_rule_note", id: item.id, label: `EMD: ${item.service_code}` })),
  ].filter((item) => item.id)

  function chooseTarget(value) {
    const [target_type, target_id] = value.split(":")
    setOverride((current) => ({ ...current, target_type, target_id }))
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/agency/airline-intelligence">Back to airline intelligence</a>
            <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.airline.airline_code}</p>
            <h2 className="text-2xl font-semibold text-slate-950">{state.airline.airline_name}</h2>
            <p className="mt-1 text-sm text-slate-600">{state.decision_support_notice}</p>
          </div>
          <section className="grid gap-4 lg:grid-cols-3">
            <Info title="Profile" rows={[["Country", state.airline.country], ["Alliance", state.airline.alliance || "None"], ["Status", state.airline.status], ["Website", state.airline.website_url || "None"]]} />
            <Info title="Published Records" rows={[["Knowledge", state.knowledge.length], ["Procedures", state.procedures.length], ["EMD notes", state.emd_notes.length], ["Agency overrides", state.overrides.length]]} />
            <Info title="Notes" rows={[["Global profile notes", state.airline.notes || "None"]]} />
          </section>
          <Panel title="Published Knowledge">
            <List items={state.knowledge} empty="No published knowledge for this airline" render={(item) => (
              <div>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <a className="font-semibold text-blue-700" href={`/agency/airline-knowledge/${item.id}`}>{item.title}</a>
                  <div className="flex flex-wrap gap-2"><KnowledgeCategoryBadge category={item.category} /><ReviewStatusBadge status={item.review_status} /><ConfidenceBadge confidence={item.confidence} /></div>
                </div>
                <p className="mt-2 text-slate-600">{item.summary}</p>
                {item.agency_override?.overrides?.length ? <p className="mt-2 text-sm font-medium text-amber-700">Agency-specific override or annotation exists.</p> : null}
              </div>
            )} />
          </Panel>
          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Procedures"><List items={state.procedures} empty="No published procedures" render={(item) => `${item.title} · ${item.channel.replaceAll("_", " ")} · ${item.procedure_type.replaceAll("_", " ")}`} /></Panel>
            <Panel title="EMD / RFIC / RFISC Notes"><List items={state.emd_notes} empty="No published EMD notes" render={(item) => `${item.service_code} · ${item.service_name} · RFIC ${item.rfic_code || "n/a"} · RFISC ${item.rfisc_code || "n/a"}`} /></Panel>
          </section>
          <Panel title="Agency Overrides / Annotations">
            <form className="grid gap-3" onSubmit={createOverride}>
              <div className="grid gap-3 md:grid-cols-[1fr_150px_1fr_auto]">
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={`${override.target_type}:${override.target_id}`} onChange={(event) => chooseTarget(event.target.value)}>
                  {targetOptions.map((item) => <option key={`${item.type}:${item.id}`} value={`${item.type}:${item.id}`}>{item.label}</option>)}
                </select>
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={override.override_mode} onChange={(event) => setOverride((current) => ({ ...current, override_mode: event.target.value }))}>{["annotate", "augment", "replace"].map((item) => <option key={item}>{item}</option>)}</select>
                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Title" value={override.title} onChange={(event) => setOverride((current) => ({ ...current, title: event.target.value }))} />
                <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={override.internal_warning} onChange={(event) => setOverride((current) => ({ ...current, internal_warning: event.target.checked }))} /> Warning</label>
              </div>
              <textarea required className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Agency-only override or annotation" value={override.override_text} onChange={(event) => setOverride((current) => ({ ...current, override_text: event.target.value }))} />
              <button className="w-fit rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Create override</button>
            </form>
            <List items={state.overrides} empty="No agency overrides yet" render={(item) => `${item.override_mode} · ${item.title || item.target_type} · ${item.status}`} />
          </Panel>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function List({ items, empty, render }) {
  if (!items?.length) return <EmptyState title={empty} body="Published platform records and agency annotations appear here." />
  return <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>)}</div>
}

function Info({ title, rows }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 break-words text-slate-600">{value}</dd></div>)}</dl></section>
}
