import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const sampleDifficulties = ["easy", "medium", "hard", "edge_case"]

export default function GdsParserPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ raw_text: "", parser_profile_id: "" })
  const [selectedRun, setSelectedRun] = useState(null)
  const [entities, setEntities] = useState([])
  const [trainingForm, setTrainingForm] = useState({ sample_title: "", difficulty: "medium", tags: "" })
  const [correctionEntity, setCorrectionEntity] = useState(null)
  const [correctionForm, setCorrectionForm] = useState({ corrected_summary: "", corrected_value: "", correction_reason: "" })
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [profiles, runs] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/gds-parser/profiles`),
      apiGet(`/api/agencies/${context.agency.id}/gds-parser/runs`),
    ])
    setState({ ...context, profiles: profiles.items || [], runs: runs.items || [] })
    const params = new URLSearchParams(window.location.search)
    const requestedRun = params.get("parser_run_id")
    if (requestedRun) {
      await openRun(context.agency.id, requestedRun)
    } else if (!selectedRun && runs.items?.length) {
      setSelectedRun(runs.items[0])
      const entityResult = await apiGet(`/api/agencies/${context.agency.id}/gds-parser/runs/${runs.items[0].id}/entities`)
      setEntities(entityResult.items || [])
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function parseText(event) {
    event.preventDefault()
    setWorking("parse")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/gds-parser/parse-text`, {
        raw_text: form.raw_text,
        parser_profile_id: form.parser_profile_id || null,
      })
      setSelectedRun(result.parser_run)
      setEntities(result.entities || [])
      setMessage("Parser run stored. Review confidence and entities before any import decision.")
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function openRun(agencyId, runId) {
    const [runResult, entityResult] = await Promise.all([
      apiGet(`/api/agencies/${agencyId}/gds-parser/runs/${runId}`),
      apiGet(`/api/agencies/${agencyId}/gds-parser/runs/${runId}/entities`),
    ])
    setSelectedRun(runResult.parser_run)
    setEntities(entityResult.items || [])
  }

  async function chooseRun(runId) {
    setWorking(runId)
    setError("")
    try {
      await openRun(state.agency.id, runId)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function applyCorrection(entity, correctionType) {
    setWorking(`${correctionType}-${entity.id}`)
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/gds-parser/corrections`, {
        parser_run_id: selectedRun.id,
        parsed_entity_id: entity.id,
        booking_import_draft_id: selectedRun.booking_import_draft_id || null,
        correction_type: correctionType,
        entity_type: entity.entity_type,
        before_json: entity.normalized_json || {},
        after_json: entity.normalized_json || {},
      })
      await openRun(state.agency.id, selectedRun.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  function startCorrection(entity) {
    setCorrectionEntity(entity)
    setCorrectionForm({
      corrected_summary: entity.normalized_json?.summary || entitySummary(entity),
      corrected_value: "",
      correction_reason: "",
    })
  }

  async function submitCorrection(event) {
    event.preventDefault()
    setWorking("correct")
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/gds-parser/corrections`, {
        parser_run_id: selectedRun.id,
        parsed_entity_id: correctionEntity.id,
        booking_import_draft_id: selectedRun.booking_import_draft_id || null,
        correction_type: "correct",
        entity_type: correctionEntity.entity_type,
        before_json: correctionEntity.normalized_json || {},
        after_json: {
          ...(correctionEntity.normalized_json || {}),
          summary: correctionForm.corrected_summary,
          corrected_value: correctionForm.corrected_value,
        },
        correction_reason: correctionForm.correction_reason,
      })
      setCorrectionEntity(null)
      await openRun(state.agency.id, selectedRun.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function createTrainingSample(event) {
    event.preventDefault()
    setWorking("sample")
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/gds-parser/runs/${selectedRun.id}/training-sample`, {
        sample_title: trainingForm.sample_title || `Parser run ${selectedRun.id}`,
        difficulty: trainingForm.difficulty,
        tags: trainingForm.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
        expected_payload_json: selectedRun.normalized_preview_json || {},
      })
      setTrainingForm({ sample_title: "", difficulty: "medium", tags: "" })
      setMessage("Training sample created for platform review.")
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  const preview = selectedRun?.normalized_preview_json || {}
  const warnings = selectedRun?.warnings_json || preview.warnings || []
  const lowConfidence = selectedRun && Number(selectedRun.overall_confidence || 0) < 0.6
  const selectedProfileOptions = useMemo(() => [["", "Auto-detect"], ...(state?.profiles || []).map((profile) => [profile.id, `${profile.title} (${label(profile.provider_family)})`])], [state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">GDS Parser</h2>
              <p className="mt-1 text-sm text-slate-600">Governed parser runs, entity confidence, corrections, and training samples. No live GDS or provider action is performed.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/booking-imports">Booking imports</a>
              {selectedRun ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={documentHref(selectedRun.id)}>Generate parse review summary</a> : null}
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
            <form className="space-y-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={parseText}>
              <div className="grid gap-3 md:grid-cols-[1fr_220px]">
                <label className="text-sm font-medium text-slate-700">
                  Raw GDS / itinerary / ticket / EMD text
                  <textarea className="mt-1 min-h-52 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" value={form.raw_text} onChange={(event) => setForm({ ...form, raw_text: event.target.value })} required />
                </label>
                <div className="space-y-3">
                  <Select label="Parser profile" value={form.parser_profile_id} options={selectedProfileOptions} onChange={(value) => setForm({ ...form, parser_profile_id: value })} />
                  <button className="aa-primary-action w-full rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "parse"}>
                    {working === "parse" ? "Parsing..." : "Parse text"}
                  </button>
                </div>
              </div>
            </form>

            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Detection</h3>
              {selectedRun ? (
                <div className="mt-4 grid gap-3">
                  <Metric label="Provider" value={label(selectedRun.provider_family_detected)} />
                  <Metric label="Format" value={label(selectedRun.input_format_detected)} />
                  <Metric label="Confidence" value={formatConfidence(selectedRun.overall_confidence)} />
                  <Metric label="Status" value={label(selectedRun.parse_status)} tone={lowConfidence ? "amber" : "slate"} />
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-500">Parse text or open a prior run.</p>
              )}
            </section>
          </section>

          {selectedRun ? (
            <>
              {warnings.length ? <WarningsPanel warnings={warnings} /> : null}
              <section className="grid gap-4 md:grid-cols-6">
                <Metric label="Passengers" value={selectedRun.extracted_passenger_count || 0} />
                <Metric label="Segments" value={selectedRun.extracted_segment_count || 0} />
                <Metric label="Tickets" value={selectedRun.extracted_ticket_count || 0} />
                <Metric label="EMDs" value={selectedRun.extracted_emd_count || 0} />
                <Metric label="SSR" value={selectedRun.extracted_ssr_count || 0} />
                <Metric label="OSI" value={selectedRun.extracted_osi_count || 0} />
              </section>

              <section className="grid gap-4 lg:grid-cols-2">
                <PreviewTable title="Passengers" items={preview.passengers || []} columns={[
                  ["Name", (item) => item.display_name || `${item.first_name || ""} ${item.last_name || ""}`.trim()],
                  ["Confidence", (item) => formatConfidence(item.confidence)],
                ]} />
                <PreviewTable title="Segments" items={preview.segments || []} columns={[
                  ["Flight", (item) => [item.marketing_airline_code, item.flight_number].filter(Boolean).join(" ")],
                  ["Route", (item) => `${item.origin_airport_code || "?"} to ${item.destination_airport_code || "?"}`],
                  ["Date", (item) => item.departure_date || "not set"],
                  ["Status", (item) => item.status || "not set"],
                ]} />
                <PreviewTable title="SSR / OSI" items={[...(preview.ssr || []), ...(preview.osi || [])]} columns={[
                  ["Type", (item) => item.ssr_code ? "SSR" : "OSI"],
                  ["Code", (item) => item.ssr_code || item.airline_code || "not set"],
                  ["Text", (item) => item.free_text || item.text || item.line || "not set"],
                ]} />
                <PreviewTable title="Tickets / EMDs" items={[...(preview.ticket_numbers || []).map((number) => ({ type: "Ticket", number })), ...(preview.emd_numbers || []).map((number) => ({ type: "EMD", number }))]} columns={[
                  ["Type", (item) => item.type],
                  ["Number", (item) => item.number],
                ]} />
                <PreviewTable title="Pricing" items={preview.pricing?.total_amount ? [preview.pricing] : []} columns={[
                  ["Currency", (item) => item.currency || "not set"],
                  ["Total", (item) => item.total_amount || "not set"],
                ]} />
                <PreviewTable title="Remarks / contact" items={preview.contacts_and_remarks || []} columns={[
                  ["Text", (item) => item.contact_text || item.remark_text || item.line || "not set"],
                ]} />
              </section>

              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-100 px-5 py-4">
                  <h3 className="font-semibold text-slate-950">Parsed entities</h3>
                </div>
                {entities.length ? (
                  <div className="divide-y divide-slate-100">
                    {entities.map((entity) => (
                      <div className="grid gap-3 p-4 text-sm lg:grid-cols-[120px_minmax(0,1fr)_90px_90px_220px]" key={entity.id}>
                        <span className="font-semibold text-slate-950">{label(entity.entity_type)}</span>
                        <span className="min-w-0">
                          <span className="block truncate text-slate-800">{entitySummary(entity)}</span>
                          <span className="block truncate text-xs text-slate-500">{entity.source_text || "No source excerpt"}</span>
                        </span>
                        <span>{formatConfidence(entity.confidence)}</span>
                        <span>{label(entity.status)}</span>
                        <span className="flex flex-wrap gap-2">
                          <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => applyCorrection(entity, "accept")} disabled={!!working}>Accept</button>
                          <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => startCorrection(entity)}>Correct</button>
                          <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => applyCorrection(entity, "reject")} disabled={!!working}>Reject</button>
                          <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => applyCorrection(entity, "ignore")} disabled={!!working}>Ignore</button>
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState title="No parsed entities" body="Low-information text can produce only warnings and a manual review run." />
                )}
              </section>

              <form className="grid gap-3 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-[1fr_180px_1fr_auto]" onSubmit={createTrainingSample}>
                <Field label="Training sample title" value={trainingForm.sample_title} onChange={(value) => setTrainingForm({ ...trainingForm, sample_title: value })} />
                <Select label="Difficulty" value={trainingForm.difficulty} options={sampleDifficulties.map((item) => [item, label(item)])} onChange={(value) => setTrainingForm({ ...trainingForm, difficulty: value })} />
                <Field label="Tags" value={trainingForm.tags} onChange={(value) => setTrainingForm({ ...trainingForm, tags: value })} />
                <button className="aa-primary-action self-end rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "sample"}>{working === "sample" ? "Creating..." : "Create training sample"}</button>
              </form>

              <details className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced parser payload</summary>
                <pre className="mt-3 max-h-80 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(selectedRun, null, 2)}</pre>
              </details>
            </>
          ) : null}

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="font-semibold text-slate-950">Parser runs history</h3>
            </div>
            {state?.runs?.length ? (
              <div className="divide-y divide-slate-100">
                {state.runs.map((run) => (
                  <button className="grid w-full gap-3 p-4 text-left text-sm hover:bg-slate-50 md:grid-cols-[160px_130px_100px_1fr_120px]" type="button" key={run.id} onClick={() => chooseRun(run.id)}>
                    <span>{run.created_at ? new Date(run.created_at).toLocaleString() : "not set"}</span>
                    <span>{label(run.parse_status)}</span>
                    <span>{formatConfidence(run.overall_confidence)}</span>
                    <span>{run.booking_import_draft_id || "Free text"}</span>
                    <span>{run.warnings_json?.length || 0} warnings</span>
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState title="No parser runs" body="Paste text in the parser console to store the first governed parser run." />
            )}
          </section>

          {correctionEntity ? (
            <CorrectionModal
              entity={correctionEntity}
              form={correctionForm}
              setForm={setCorrectionForm}
              onClose={() => setCorrectionEntity(null)}
              onSubmit={submitCorrection}
              working={working === "correct"}
            />
          ) : null}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function CorrectionModal({ entity, form, setForm, onClose, onSubmit, working }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <form className="w-full max-w-lg space-y-4 rounded-lg bg-white p-5 shadow-xl" onSubmit={onSubmit}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">{label(entity.entity_type)}</p>
            <h3 className="text-xl font-semibold text-slate-950">Correct extracted entity</h3>
          </div>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onClose}>Close</button>
        </div>
        <Field label="Corrected summary" value={form.corrected_summary} onChange={(value) => setForm({ ...form, corrected_summary: value })} />
        <Field label="Corrected value" value={form.corrected_value} onChange={(value) => setForm({ ...form, corrected_value: value })} />
        <TextArea label="Correction reason" value={form.correction_reason} onChange={(value) => setForm({ ...form, correction_reason: value })} />
        <details className="rounded-md border border-slate-200 bg-slate-50 p-3">
          <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced source JSON</summary>
          <pre className="mt-3 max-h-48 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(entity.normalized_json || {}, null, 2)}</pre>
        </details>
        <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working}>{working ? "Saving..." : "Save correction"}</button>
      </form>
    </div>
  )
}

function PreviewTable({ columns, items, title }) {
  return (
    <section className="min-w-0 rounded-lg border border-slate-200 bg-white p-4">
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
    <section className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <h3 className="font-semibold text-amber-950">Warnings</h3>
      <div className="mt-2 grid gap-2 md:grid-cols-2">
        {warnings.map((warning, index) => <p className="text-sm text-amber-800" key={warning.code || index}>{warning.message || warning.code || String(warning)}</p>)}
      </div>
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

function TextArea({ label: fieldLabel, value, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <textarea className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label: fieldLabel, value, options, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => <option value={optionValue} key={optionValue}>{optionLabel}</option>)}
      </select>
    </label>
  )
}

function Metric({ label: metricLabel, value, tone = "slate" }) {
  const toneClass = tone === "amber" ? "border-amber-200 bg-amber-50 text-amber-950" : "border-slate-200 bg-white text-slate-950"
  return (
    <div className={`rounded-lg border p-4 ${toneClass}`}>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metricLabel}</p>
      <p className="mt-2 text-lg font-semibold">{value}</p>
    </div>
  )
}

function entitySummary(entity) {
  return entity?.normalized_json?.summary || entity?.normalized_json?.display_name || entity?.normalized_json?.number || entity?.source_text || "Extracted entity"
}

function formatConfidence(value) {
  if (value === null || value === undefined || value === "") return "not set"
  const number = Number(value)
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : String(value)
}

function label(value) {
  return String(value || "not set").replaceAll("_", " ")
}

function documentHref(parserRunId) {
  const params = new URLSearchParams({
    document_type: "gds_parse_review_summary",
    source_context_type: "gds_parser_run",
    source_context_id: parserRunId,
  })
  return `/agency/documents?${params.toString()}`
}
