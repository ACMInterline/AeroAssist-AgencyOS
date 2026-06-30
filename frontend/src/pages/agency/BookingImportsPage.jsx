import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const sourceTypes = ["cryptic_gds", "itinerary_confirmation_text", "manual_text", "email_import", "pdf_import", "other"]
const importContexts = ["new_booking", "existing_trip_change", "standalone_ticket", "standalone_emd", "other"]

export default function BookingImportsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({
    source_type: "cryptic_gds",
    import_context: "new_booking",
    linked_trip_id: "",
    raw_text: "",
  })
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const drafts = await apiGet(`/api/agencies/${context.agency.id}/booking-import-drafts`)
    setState({ ...context, drafts: drafts.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function createDraft(event) {
    event.preventDefault()
    setWorking("create")
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/booking-import-drafts`, {
        source_type: form.source_type,
        import_context: form.import_context,
        linked_trip_id: form.linked_trip_id || null,
        raw_text: form.raw_text,
      })
      setForm({ ...form, raw_text: "" })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function parseDraft(id) {
    setWorking(id)
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/gds-parser/booking-import-drafts/${id}/parse`, {})
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function importDraft(id) {
    setWorking(id)
    setError("")
    try {
      const created = await apiPost(`/api/agencies/${state.agency.id}/booking-import-drafts/${id}/import-as-booking`, {
        create_draft_record: true,
        create_ticket_mirrors: true,
        create_emd_mirrors: true,
      })
      window.location.href = `/agency/booking-workspaces/${created.booking_workspace.id}`
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="text-2xl font-semibold text-slate-950">Booking Imports</h2>
              <p className="mt-1 text-sm text-slate-600">Import data into internal booking, ticket, and EMD mirrors only. No provider action is performed.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/gds-parser">GDS Parser</a>
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/documents?document_type=import_review_summary&source_context_type=booking_import_draft">Documents</a>
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/booking-workspaces">Booking workspaces</a>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <form className="space-y-4 rounded-lg border border-slate-200 bg-white p-4" onSubmit={createDraft}>
            <div className="grid gap-3 md:grid-cols-3">
              <Select label="Source type" value={form.source_type} options={sourceTypes} onChange={(value) => setForm({ ...form, source_type: value })} />
              <Select label="Import context" value={form.import_context} options={importContexts} onChange={(value) => setForm({ ...form, import_context: value })} />
              <Field label="Existing trip id/reference" value={form.linked_trip_id} onChange={(value) => setForm({ ...form, linked_trip_id: value })} />
            </div>
            <label className="block text-sm font-medium text-slate-700">
              Raw GDS / itinerary confirmation text
              <textarea className="mt-1 min-h-40 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" value={form.raw_text} onChange={(event) => setForm({ ...form, raw_text: event.target.value })} required />
            </label>
            <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "create"}>{working === "create" ? "Creating..." : "Create import draft"}</button>
          </form>

          {state?.drafts?.length ? (
            <div className="space-y-3">
              {state.drafts.map((draft) => <DraftCard draft={draft} key={draft.id} onImport={importDraft} onParse={parseDraft} working={working === draft.id} />)}
            </div>
          ) : (
            <EmptyState title="No booking import drafts" body="Paste cryptic GDS or confirmation text to stage a reviewed internal mirror import." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function DraftCard({ draft, onImport, onParse, working }) {
  const parsed = draft.normalized_preview_json || draft.parsed_json || {}
  const warnings = draft.warnings_json || parsed.warnings || []
  const entityCounts = draft.parsed_entity_counts_json || {}
  const lowConfidence = draft.overall_confidence !== null && draft.overall_confidence !== undefined && Number(draft.overall_confidence) < 0.6
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label(draft.source_type)} · {label(draft.import_context)}</p>
          <h3 className="mt-1 text-lg font-semibold text-slate-950">{parsed.record_locator || "Unparsed import draft"}</h3>
          <p className="mt-1 text-sm text-slate-600">{label(draft.parser_status)} · {draft.linked_trip_id || "No trip link"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => onParse(draft.id)} disabled={working}>{working ? "Working..." : "Parse with GDS Parser"}</button>
          {draft.latest_parser_run_id ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/gds-parser?parser_run_id=${draft.latest_parser_run_id}`}>{lowConfidence ? "Correct low-confidence parse" : "Open parser run"}</a> : null}
          <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={documentHref("booking_import_review_summary", "booking_import_draft", draft.id)}>Review document</a>
          <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={() => onImport(draft.id)} disabled={working}>{working ? "Working..." : "Import as manual booking"}</button>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-7">
        <Metric label="Confidence" value={formatConfidence(draft.overall_confidence || parsed.overall_confidence)} tone={lowConfidence ? "amber" : "slate"} />
        <Metric label="Run status" value={label(parsed.parse_status || draft.parser_status)} />
        <Metric label="Passengers" value={entityCounts.passengers ?? (parsed.passengers || []).length} />
        <Metric label="Segments" value={entityCounts.segments ?? (parsed.segments || []).length} />
        <Metric label="SSR" value={entityCounts.ssr ?? (parsed.ssr || []).length} />
        <Metric label="Tickets" value={entityCounts.tickets ?? (parsed.ticket_numbers || []).length} />
        <Metric label="EMDs" value={entityCounts.emds ?? (parsed.emd_numbers || []).length} />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <PreviewTable title="Passengers" items={parsed.passengers || []} columns={[
          ["Name", (item) => item.display_name || item.name || `${item.first_name || ""} ${item.last_name || ""}`.trim() || item.raw || "Passenger"],
          ["Type", (item) => item.passenger_type || item.type || "not set"],
        ]} />
        <PreviewTable title="Segments" items={parsed.segments || []} columns={[
          ["Flight", (item) => [item.marketing_airline_code || item.airline, item.flight_number].filter(Boolean).join(" ") || item.raw || "Flight"],
          ["Route", (item) => `${item.origin_airport_code || item.origin || "?"} to ${item.destination_airport_code || item.destination || "?"}`],
          ["Date", (item) => item.departure_date || item.date || "not set"],
        ]} />
        <PreviewTable title="SSR / OSI" items={[...(parsed.ssr || []), ...(parsed.osi || [])]} columns={[
          ["Type", (item) => item.ssr_code ? "SSR" : "OSI"],
          ["Code / airline", (item) => item.ssr_code || item.airline_code || item.airline || "not set"],
          ["Text", (item) => item.free_text || item.text || item.raw || "not set"],
        ]} />
        <PreviewTable title="Ticket numbers" items={(parsed.ticket_numbers || []).map((number) => ({ number }))} columns={[
          ["Ticket", (item) => item.number],
        ]} />
        <PreviewTable title="EMD numbers" items={(parsed.emd_numbers || []).map((number) => ({ number }))} columns={[
          ["EMD", (item) => item.number],
        ]} />
        <WarningsPanel warnings={warnings} />
      </div>
      <details className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3">
        <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced parsed JSON</summary>
        <pre className="mt-3 max-h-56 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(parsed, null, 2)}</pre>
      </details>
    </section>
  )
}

function PreviewTable({ columns, items, title }) {
  return (
    <section className="min-w-0">
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      {items.length ? (
        <div className="mt-2 overflow-hidden rounded-md border border-slate-200">
          <div className="grid gap-2 bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500" style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr))` }}>
            {columns.map(([heading]) => <span key={heading}>{heading}</span>)}
          </div>
          <div className="divide-y divide-slate-100">
            {items.map((item, index) => (
              <div className="grid gap-2 px-3 py-2 text-sm text-slate-700" key={item.id || item.number || index} style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr))` }}>
                {columns.map(([heading, render]) => <span className="truncate" key={heading}>{render(item)}</span>)}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="mt-2 rounded-md border border-dashed border-slate-200 px-3 py-2 text-sm text-slate-500">None found.</p>
      )}
    </section>
  )
}

function WarningsPanel({ warnings }) {
  return (
    <section>
      <h4 className="text-sm font-semibold text-slate-950">Warnings</h4>
      {warnings.length ? (
        <div className="mt-2 space-y-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          {warnings.map((warning, index) => <p key={warning.code || index}>{warning.message || warning.code || String(warning)}</p>)}
        </div>
      ) : (
        <p className="mt-2 rounded-md border border-dashed border-slate-200 px-3 py-2 text-sm text-slate-500">None found.</p>
      )}
    </section>
  )
}

function Field({ label: fieldLabel, value, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label: fieldLabel, value, options, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option value={option} key={option}>{label(option)}</option>)}
      </select>
    </label>
  )
}

function Metric({ label: metricLabel, value, tone = "slate" }) {
  const toneClass = tone === "amber" ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-slate-50"
  return (
    <div className={`rounded-md border px-3 py-2 ${toneClass}`}>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metricLabel}</p>
      <p className="mt-1 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function formatConfidence(value) {
  if (value === null || value === undefined || value === "") return "not set"
  const number = Number(value)
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : String(value)
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function documentHref(documentType, sourceContextType, sourceContextId) {
  const params = new URLSearchParams({
    document_type: documentType,
    source_context_type: sourceContextType,
    source_context_id: sourceContextId || "",
  })
  return `/agency/documents?${params.toString()}`
}
