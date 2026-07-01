import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const sourceTypes = ["pasted_text", "uploaded_text", "airline_website_copy", "trade_support_copy", "gds_helpdesk_copy", "email_policy_copy", "manual_note", "other"]
const candidateTabs = [
  ["rules", "Rules"],
  ["prices", "Pricing"],
  ["communication_rules", "SSR/OSI"],
  ["emd_rules", "EMD / RFIC"],
  ["exceptions", "Exceptions"],
]

export default function AirlinePolicyIngestionPage() {
  const [state, setState] = useState(null)
  const [selectedSource, setSelectedSource] = useState(null)
  const [detail, setDetail] = useState(null)
  const [tab, setTab] = useState("rules")
  const [form, setForm] = useState({
    airline_iata_code: "",
    airline_name_snapshot: "",
    service_domain: "special_services",
    service_family: "unaccompanied_minor",
    source_title: "",
    source_type: "pasted_text",
    source_url: "",
    source_date: "",
    effective_from: "",
    effective_to: "",
    raw_text: "",
  })
  const [correctionTarget, setCorrectionTarget] = useState(null)
  const [correctionForm, setCorrectionForm] = useState({ corrected_summary: "", correction_reason: "" })
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(openSourceId = selectedSource?.id) {
    const [summary, sources, approved] = await Promise.all([
      apiGet("/api/platform/summary"),
      apiGet("/api/platform/airline-policy/sources"),
      apiGet("/api/platform/airline-policy/approved-knowledge"),
    ])
    setState({ summary, sources: sources.items || [], approved: approved.items || [] })
    const nextSource = (sources.items || []).find((item) => item.id === openSourceId) || (sources.items || [])[0] || null
    if (nextSource) {
      await openSource(nextSource.id, false)
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function openSource(sourceId, updateSelection = true) {
    const result = await apiGet(`/api/platform/airline-policy/sources/${sourceId}`)
    if (updateSelection) {
      setSelectedSource(result.policy_source)
    } else {
      setSelectedSource(result.policy_source)
    }
    setDetail(result)
  }

  async function createSource(event) {
    event.preventDefault()
    setWorking("create")
    setError("")
    setMessage("")
    try {
      const payload = cleanPayload(form)
      const created = await apiPost("/api/platform/airline-policy/sources", payload)
      setMessage("Policy source created. Detect sections or run extraction when ready.")
      setForm({ ...form, source_title: "", raw_text: "", source_url: "" })
      await load(created.policy_source.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function detectSections() {
    if (!selectedSource) return
    setWorking("sections")
    setError("")
    try {
      await apiPost(`/api/platform/airline-policy/sources/${selectedSource.id}/detect-sections`, {})
      setMessage("Sections detected.")
      await load(selectedSource.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function runExtraction() {
    if (!selectedSource) return
    setWorking("extract")
    setError("")
    try {
      await apiPost(`/api/platform/airline-policy/sources/${selectedSource.id}/extract`, {
        service_domain: selectedSource.service_domain || form.service_domain,
        service_family: selectedSource.service_family || form.service_family,
      })
      setMessage("Extraction run stored. Review candidates before promotion.")
      await load(selectedSource.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function reviewCandidate(candidate, targetType, correctionType) {
    if (!selectedSource) return
    setWorking(`${correctionType}-${candidate.id}`)
    setError("")
    try {
      await apiPost("/api/platform/airline-policy/review-corrections", {
        policy_source_id: selectedSource.id,
        extraction_run_id: candidate.extraction_run_id,
        target_type: targetType,
        target_id: candidate.id,
        correction_type: correctionType,
        before_json: candidateSummaryPayload(candidate),
        after_json: candidateSummaryPayload(candidate),
        correction_reason: `Platform ${label(correctionType)} review.`,
      })
      await load(selectedSource.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  function startCorrection(candidate, targetType) {
    setCorrectionTarget({ candidate, targetType })
    setCorrectionForm({ corrected_summary: candidateSummary(candidate), correction_reason: "" })
  }

  async function submitCorrection(event) {
    event.preventDefault()
    if (!correctionTarget || !selectedSource) return
    setWorking("correct")
    setError("")
    try {
      const { candidate, targetType } = correctionTarget
      await apiPost("/api/platform/airline-policy/review-corrections", {
        policy_source_id: selectedSource.id,
        extraction_run_id: candidate.extraction_run_id,
        target_type: targetType,
        target_id: candidate.id,
        correction_type: "correct",
        before_json: candidateSummaryPayload(candidate),
        after_json: { ...candidateSummaryPayload(candidate), corrected_summary: correctionForm.corrected_summary },
        correction_reason: correctionForm.correction_reason,
      })
      setCorrectionTarget(null)
      await load(selectedSource.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function promoteCandidate(candidate, targetType) {
    if (!selectedSource) return
    setWorking(`promote-${candidate.id}`)
    setError("")
    try {
      await apiPost("/api/platform/airline-policy/promote-candidate", {
        policy_source_id: selectedSource.id,
        extraction_run_id: candidate.extraction_run_id,
        target_type: targetType,
        target_id: candidate.id,
        knowledge_type: knowledgeTypeFor(targetType),
      })
      setMessage("Accepted candidate promoted to approved policy knowledge.")
      await load(selectedSource.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  const candidates = detail?.candidates || {}
  const selectedItems = candidates[tab] || []
  const latestRun = useMemo(() => (detail?.extraction_runs || [])[0], [detail])

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Policy</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Policy Ingestion</h2>
              <p className="mt-1 text-sm text-slate-600">Govern pasted policy text into reviewed source records, extraction candidates, corrections, and approved knowledge.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={detectSections} disabled={!selectedSource || working === "sections"}>{working === "sections" ? "Detecting..." : "Detect sections"}</button>
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={runExtraction} disabled={!selectedSource || working === "extract"}>{working === "extract" ? "Extracting..." : "Run extraction"}</button>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-4 md:grid-cols-4">
            <Metric label="Sources" value={state?.sources?.length || 0} />
            <Metric label="Sections" value={detail?.sections?.length || 0} />
            <Metric label="Latest confidence" value={formatConfidence(latestRun?.overall_confidence)} />
            <Metric label="Approved records" value={state?.approved?.length || 0} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createSource}>
                <h3 className="font-semibold text-slate-950">New policy source</h3>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-1">
                  <Field label="Airline code" value={form.airline_iata_code} onChange={(value) => setForm({ ...form, airline_iata_code: value.toUpperCase() })} />
                  <Field label="Airline name" value={form.airline_name_snapshot} onChange={(value) => setForm({ ...form, airline_name_snapshot: value })} />
                  <Field label="Service domain" value={form.service_domain} onChange={(value) => setForm({ ...form, service_domain: value })} />
                  <Field label="Service family" value={form.service_family} onChange={(value) => setForm({ ...form, service_family: value })} />
                  <Field label="Source title" value={form.source_title} onChange={(value) => setForm({ ...form, source_title: value })} required />
                  <Select label="Source type" value={form.source_type} options={sourceTypes.map((item) => [item, label(item)])} onChange={(value) => setForm({ ...form, source_type: value })} />
                  <Field label="Source URL" value={form.source_url} onChange={(value) => setForm({ ...form, source_url: value })} />
                </div>
                <TextArea label="Paste policy text" value={form.raw_text} onChange={(value) => setForm({ ...form, raw_text: value })} required />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "create"}>{working === "create" ? "Creating..." : "Create policy source"}</button>
              </form>

              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-100 px-5 py-4">
                  <h3 className="font-semibold text-slate-950">Policy sources</h3>
                </div>
                {state?.sources?.length ? (
                  <div className="divide-y divide-slate-100">
                    {state.sources.map((source) => (
                      <button className={`w-full px-5 py-4 text-left text-sm hover:bg-slate-50 ${source.id === selectedSource?.id ? "bg-blue-50" : ""}`} type="button" key={source.id} onClick={() => openSource(source.id)}>
                        <span className="block font-semibold text-slate-950">{source.source_title}</span>
                        <span className="text-slate-600">{source.airline_iata_code || source.airline_name_snapshot || "Airline not set"} · {label(source.service_family)}</span>
                        <span className="mt-1 block text-xs text-slate-500">{label(source.ingestion_status)} · {source.created_at ? new Date(source.created_at).toLocaleDateString() : "not dated"}</span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <EmptyState title="No policy sources" body="Create the first governed pasted policy source." />
                )}
              </section>
            </div>

            <div className="space-y-4">
              {selectedSource ? (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-950">{selectedSource.source_title}</h3>
                        <p className="mt-1 text-sm text-slate-600">{selectedSource.airline_iata_code || selectedSource.airline_name_snapshot || "Airline not linked"} · {label(selectedSource.service_domain)} · {label(selectedSource.service_family)}</p>
                      </div>
                      <StatusBadge value={selectedSource.ingestion_status} />
                    </div>
                    <div className="mt-4 grid gap-3 md:grid-cols-4">
                      <Metric label="Status" value={label(selectedSource.ingestion_status)} compact />
                      <Metric label="Confidence" value={formatConfidence(selectedSource.confidence_overall)} compact />
                      <Metric label="Warnings" value={selectedSource.warnings_json?.length || 0} compact />
                      <Metric label="Raw hash" value={(selectedSource.raw_text_hash || "").slice(0, 8) || "not set"} compact />
                    </div>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-100 px-5 py-4">
                      <h3 className="font-semibold text-slate-950">Detected sections</h3>
                    </div>
                    {detail?.sections?.length ? (
                      <div className="grid gap-3 p-4 md:grid-cols-2">
                        {detail.sections.map((section) => (
                          <div className="rounded-md border border-slate-200 p-3 text-sm" key={section.id}>
                            <div className="flex justify-between gap-3">
                              <span className="font-semibold text-slate-950">{section.section_title}</span>
                              <span className="text-xs text-slate-500">{formatConfidence(section.confidence)}</span>
                            </div>
                            <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-blue-700">{label(section.detected_category)}</p>
                            <p className="mt-2 line-clamp-3 text-slate-600">{section.section_text}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState title="No sections detected" body="Run section detection before reviewing candidates." />
                    )}
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-100 px-5 py-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <h3 className="font-semibold text-slate-950">Candidate review</h3>
                        <span className="text-sm text-slate-500">Latest run: {latestRun ? label(latestRun.extraction_status) : "none"}</span>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {candidateTabs.map(([key, title]) => (
                          <button className={`rounded-md px-3 py-2 text-sm font-semibold ${tab === key ? "bg-blue-600 text-white" : "border border-slate-300 text-slate-700"}`} type="button" key={key} onClick={() => setTab(key)}>
                            {title} ({(candidates[key] || []).length})
                          </button>
                        ))}
                      </div>
                    </div>
                    {selectedItems.length ? (
                      <div className="divide-y divide-slate-100">
                        {selectedItems.map((candidate) => (
                          <CandidateRow
                            candidate={candidate}
                            targetType={targetTypeForTab(tab)}
                            key={candidate.id}
                            onAccept={() => reviewCandidate(candidate, targetTypeForTab(tab), "accept")}
                            onCorrect={() => startCorrection(candidate, targetTypeForTab(tab))}
                            onReject={() => reviewCandidate(candidate, targetTypeForTab(tab), "reject")}
                            onPromote={() => promoteCandidate(candidate, targetTypeForTab(tab))}
                            working={working}
                          />
                        ))}
                      </div>
                    ) : (
                      <EmptyState title="No candidates in this tab" body="Run extraction or switch to another candidate category." />
                    )}
                  </section>

                  <details className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                    <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced source JSON</summary>
                    <pre className="mt-3 max-h-80 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(detail, null, 2)}</pre>
                  </details>
                </>
              ) : (
                <EmptyState title="No policy source selected" body="Create or open a source to review sections and extraction candidates." />
              )}
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="font-semibold text-slate-950">Approved knowledge</h3>
            </div>
            {state?.approved?.length ? (
              <div className="divide-y divide-slate-100">
                {state.approved.map((item) => (
                  <div className="grid gap-3 p-4 text-sm md:grid-cols-[140px_160px_1fr_120px]" key={item.id}>
                    <span className="font-semibold text-slate-950">{label(item.knowledge_type)}</span>
                    <span>{label(item.service_family)}</span>
                    <span className="text-slate-600">{item.source_excerpt || summaryFromPayload(item.normalized_payload_json)}</span>
                    <span>{item.approved_at ? new Date(item.approved_at).toLocaleDateString() : "not dated"}</span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No approved knowledge" body="Accepted candidates can be explicitly promoted after platform review." />
            )}
          </section>

          {correctionTarget ? (
            <CorrectionModal
              form={correctionForm}
              setForm={setCorrectionForm}
              target={correctionTarget}
              onClose={() => setCorrectionTarget(null)}
              onSubmit={submitCorrection}
              working={working === "correct"}
            />
          ) : null}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function CandidateRow({ candidate, targetType, onAccept, onCorrect, onReject, onPromote, working }) {
  const promotable = ["accepted", "corrected"].includes(candidate.status)
  return (
    <div className="grid gap-3 p-4 text-sm lg:grid-cols-[150px_minmax(0,1fr)_90px_100px_260px]">
      <span className="font-semibold text-slate-950">{candidateType(candidate, targetType)}</span>
      <span className="min-w-0">
        <span className="block truncate text-slate-800">{candidateSummary(candidate)}</span>
        <span className="block truncate text-xs text-slate-500">{candidate.source_excerpt || "No source excerpt"}</span>
      </span>
      <span>{formatConfidence(candidate.confidence)}</span>
      <span>{label(candidate.status)}</span>
      <span className="flex flex-wrap gap-2">
        <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={onAccept} disabled={!!working}>Accept</button>
        <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={onCorrect}>Correct</button>
        <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={onReject} disabled={!!working}>Reject</button>
        <button className="aa-primary-action rounded-md px-2 py-1 text-xs font-semibold disabled:opacity-60" type="button" onClick={onPromote} disabled={!promotable || !!working}>Promote</button>
      </span>
    </div>
  )
}

function CorrectionModal({ target, form, setForm, onClose, onSubmit, working }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <form className="w-full max-w-lg space-y-4 rounded-lg bg-white p-5 shadow-xl" onSubmit={onSubmit}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">{label(target.targetType)}</p>
            <h3 className="text-xl font-semibold text-slate-950">Correct policy candidate</h3>
          </div>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onClose}>Close</button>
        </div>
        <Field label="Corrected summary" value={form.corrected_summary} onChange={(value) => setForm({ ...form, corrected_summary: value })} />
        <TextArea label="Correction reason" value={form.correction_reason} onChange={(value) => setForm({ ...form, correction_reason: value })} />
        <details className="rounded-md border border-slate-200 bg-slate-50 p-3">
          <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced candidate JSON</summary>
          <pre className="mt-3 max-h-48 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(target.candidate || {}, null, 2)}</pre>
        </details>
        <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working}>{working ? "Saving..." : "Save correction"}</button>
      </form>
    </div>
  )
}

function Field({ label: fieldLabel, value, onChange, required = false }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} required={required} />
    </label>
  )
}

function TextArea({ label: fieldLabel, value, onChange, required = false }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <textarea className="mt-1 min-h-36 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} required={required} />
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

function Metric({ label: metricLabel, value, compact = false }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metricLabel}</p>
      <p className={`mt-2 font-semibold text-slate-950 ${compact ? "text-base" : "text-2xl"}`}>{value}</p>
    </div>
  )
}

function StatusBadge({ value }) {
  return <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{label(value)}</span>
}

function cleanPayload(payload) {
  const clean = { ...payload }
  for (const key of ["source_url", "source_date", "effective_from", "effective_to", "airline_iata_code", "airline_name_snapshot"]) {
    if (!clean[key]) clean[key] = null
  }
  return clean
}

function targetTypeForTab(value) {
  return { rules: "rule", prices: "price", communication_rules: "communication_rule", emd_rules: "emd_rule", exceptions: "exception" }[value] || "rule"
}

function knowledgeTypeFor(targetType) {
  return { rule: "applicability_rule", price: "pricing_rule", communication_rule: "communication_rule", emd_rule: "emd_rule", exception: "exception_rule" }[targetType] || "operational_requirement"
}

function candidateType(candidate, targetType) {
  return label(candidate.rule_type || candidate.price_type || candidate.communication_type || candidate.emd_type || candidate.exception_type || targetType)
}

function candidateSummary(candidate) {
  if (candidate.amount) return `${candidate.currency || ""} ${candidate.amount} ${label(candidate.price_basis)}`
  if (candidate.ssr_code || candidate.osi_keyword) return [candidate.communication_type, candidate.ssr_code || candidate.osi_keyword].filter(Boolean).join(" ")
  if (candidate.rfic || candidate.rfisc) return [candidate.emd_type, candidate.rfic, candidate.rfisc].filter(Boolean).join(" / ")
  if (candidate.normalized_condition_json?.age_min || candidate.normalized_condition_json?.age_max) return `Ages ${candidate.normalized_condition_json.age_min || "?"} to ${candidate.normalized_condition_json.age_max || "?"}`
  return candidate.source_excerpt || candidate.id || "Policy candidate"
}

function candidateSummaryPayload(candidate) {
  return {
    summary: candidateSummary(candidate),
    source_excerpt: candidate.source_excerpt,
    normalized_condition_json: candidate.normalized_condition_json || {},
    normalized_action_json: candidate.normalized_action_json || {},
  }
}

function summaryFromPayload(payload) {
  if (!payload) return "Approved policy record"
  return payload.ssr_code || payload.price_type || payload.rule_type || payload.exception_type || "Approved policy record"
}

function formatConfidence(value) {
  if (value === null || value === undefined || value === "") return "not set"
  const number = Number(value)
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : String(value)
}

function label(value) {
  return String(value || "not set").replaceAll("_", " ")
}
