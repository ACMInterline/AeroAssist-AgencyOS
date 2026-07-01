import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const candidateTabs = [
  ["rules", "Rules"],
  ["prices", "Pricing"],
  ["communication_rules", "SSR/OSI"],
  ["emd_rules", "EMD"],
  ["exceptions", "Exceptions"],
]

export default function AirlinePolicyLibraryPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ airline_id: "", service_domain: "", service_family: "", knowledge_type: "" })
  const [form, setForm] = useState({
    airline_iata_code: "",
    airline_name_snapshot: "",
    service_family: "unaccompanied_minor",
    source_title: "",
    raw_text: "",
    notes: "",
  })
  const [selectedSource, setSelectedSource] = useState(null)
  const [detail, setDetail] = useState(null)
  const [tab, setTab] = useState("rules")
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(openSourceId = selectedSource?.id, nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = new URLSearchParams(Object.entries(nextFilters).filter(([, value]) => value)).toString()
    const [library, sources] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/airline-policy/library${query ? `?${query}` : ""}`),
      apiGet(`/api/agencies/${context.agency.id}/airline-policy/sources`),
    ])
    setState({ ...context, library, sources: sources.items || [] })
    const nextSource = (sources.items || []).find((item) => item.id === openSourceId) || (sources.items || [])[0] || null
    if (nextSource) {
      await openSource(context.agency.id, nextSource.id)
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function openSource(agencyId, sourceId) {
    const result = await apiGet(`/api/agencies/${agencyId}/airline-policy/sources/${sourceId}`)
    setSelectedSource(result.policy_source)
    setDetail(result)
  }

  async function applyFilters(event) {
    event.preventDefault()
    setError("")
    await load(selectedSource?.id, filters)
  }

  async function createSource(event) {
    event.preventDefault()
    setWorking("create")
    setError("")
    setMessage("")
    try {
      const created = await apiPost(`/api/agencies/${state.agency.id}/airline-policy/sources`, {
        airline_iata_code: form.airline_iata_code || null,
        airline_name_snapshot: form.airline_name_snapshot || null,
        service_domain: "special_services",
        service_family: form.service_family,
        source_title: form.source_title,
        source_type: "pasted_text",
        raw_text: form.raw_text,
        notes: form.notes || null,
      })
      setMessage("Local policy source created.")
      setForm({ ...form, source_title: "", raw_text: "", notes: "" })
      await load(created.policy_source.id)
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
      await apiPost(`/api/agencies/${state.agency.id}/airline-policy/sources/${selectedSource.id}/extract`, {
        service_domain: selectedSource.service_domain || "special_services",
        service_family: selectedSource.service_family || "general",
      })
      setMessage("Local extraction run stored. Review candidates before submitting for platform review.")
      await load(selectedSource.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function reviewCandidate(candidate, targetType, correctionType) {
    setWorking(`${correctionType}-${candidate.id}`)
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/airline-policy/review-corrections`, {
        policy_source_id: selectedSource.id,
        extraction_run_id: candidate.extraction_run_id,
        target_type: targetType,
        target_id: candidate.id,
        correction_type: correctionType,
        before_json: { summary: candidateSummary(candidate) },
        after_json: { summary: candidateSummary(candidate) },
        correction_reason: `Agency ${label(correctionType)} review.`,
      })
      await load(selectedSource.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function submitForPlatformReview() {
    if (!selectedSource) return
    setWorking("submit")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/airline-policy/sources/${selectedSource.id}/submit-for-platform-review`, {})
      if (result.global_knowledge_created === false) {
        setMessage("Local policy source submitted for platform review. No global knowledge was created automatically.")
      }
      await load(selectedSource.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  const approved = state?.library?.approved_knowledge || []
  const localSources = state?.sources || []
  const candidates = detail?.candidates || {}
  const selectedItems = candidates[tab] || []
  const latestRun = useMemo(() => (detail?.extraction_runs || [])[0], [detail])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Policy Library</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Policy Library</h2>
              <p className="mt-1 text-sm text-slate-600">Read approved platform policy knowledge and review local policy text before platform submission.</p>
            </div>
            <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={runExtraction} disabled={!selectedSource || working === "extract"}>{working === "extract" ? "Extracting..." : "Run local extraction"}</button>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-4 md:grid-cols-4">
            <Metric label="Approved records" value={approved.length} />
            <Metric label="Local sources" value={localSources.length} />
            <Metric label="Latest status" value={label(latestRun?.extraction_status)} />
            <Metric label="Agency promotion" value="disabled" />
          </section>

          <section className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <h3 className="font-semibold text-blue-950">Comparison-ready foundation</h3>
            <p className="mt-1 text-sm text-blue-800">These records are governed ingestion and review foundations. Approved knowledge will feed formal airline comparison, SSR/OSI, EMD, pricing, and exception workflows in later phases.</p>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="font-semibold text-slate-950">Approved platform policy library</h3>
              <form className="mt-3 grid gap-3 md:grid-cols-[1fr_1fr_1fr_1fr_auto]" onSubmit={applyFilters}>
                <Field label="Airline id" value={filters.airline_id} onChange={(value) => setFilters({ ...filters, airline_id: value })} />
                <Field label="Service domain" value={filters.service_domain} onChange={(value) => setFilters({ ...filters, service_domain: value })} />
                <Field label="Service family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
                <Field label="Knowledge type" value={filters.knowledge_type} onChange={(value) => setFilters({ ...filters, knowledge_type: value })} />
                <button className="self-end rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="submit">Filter</button>
              </form>
            </div>
            {approved.length ? (
              <div className="divide-y divide-slate-100">
                {approved.map((item) => (
                  <div className="grid gap-3 p-4 text-sm lg:grid-cols-[150px_160px_minmax(0,1fr)_140px]" key={item.id}>
                    <span className="font-semibold text-slate-950">{label(item.knowledge_type)}</span>
                    <span>{label(item.service_family)}</span>
                    <span className="text-slate-600">{item.source_excerpt || summaryFromPayload(item.normalized_payload_json)}</span>
                    <span>{item.approved_at ? new Date(item.approved_at).toLocaleDateString() : "not dated"}</span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No approved policy knowledge" body="Platform-approved policy knowledge will appear here as read-only library records." />
            )}
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createSource}>
                <h3 className="font-semibold text-slate-950">Submit policy text</h3>
                <Field label="Airline code" value={form.airline_iata_code} onChange={(value) => setForm({ ...form, airline_iata_code: value.toUpperCase() })} />
                <Field label="Airline name" value={form.airline_name_snapshot} onChange={(value) => setForm({ ...form, airline_name_snapshot: value })} />
                <Field label="Service family" value={form.service_family} onChange={(value) => setForm({ ...form, service_family: value })} />
                <Field label="Source title" value={form.source_title} onChange={(value) => setForm({ ...form, source_title: value })} required />
                <TextArea label="Pasted policy text" value={form.raw_text} onChange={(value) => setForm({ ...form, raw_text: value })} required />
                <TextArea label="Notes" value={form.notes} onChange={(value) => setForm({ ...form, notes: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "create"}>{working === "create" ? "Submitting..." : "Create local source"}</button>
              </form>

              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-100 px-5 py-4">
                  <h3 className="font-semibold text-slate-950">Local policy sources</h3>
                </div>
                {localSources.length ? (
                  <div className="divide-y divide-slate-100">
                    {localSources.map((source) => (
                      <button className={`w-full px-5 py-4 text-left text-sm hover:bg-slate-50 ${source.id === selectedSource?.id ? "bg-blue-50" : ""}`} type="button" key={source.id} onClick={() => openSource(state.agency.id, source.id)}>
                        <span className="block font-semibold text-slate-950">{source.source_title}</span>
                        <span className="text-slate-600">{source.airline_iata_code || source.airline_name_snapshot || "Airline not set"} · {label(source.service_family)}</span>
                        <span className="mt-1 block text-xs text-slate-500">{label(source.ingestion_status)} · {source.created_at ? new Date(source.created_at).toLocaleDateString() : "not dated"}</span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <EmptyState title="No local policy sources" body="Paste airline policy text to create an agency-local source record." />
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
                        <p className="mt-1 text-sm text-slate-600">{selectedSource.airline_iata_code || selectedSource.airline_name_snapshot || "Airline not linked"} · {label(selectedSource.ingestion_status)}</p>
                      </div>
                      <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={submitForPlatformReview} disabled={working === "submit"}>{working === "submit" ? "Submitting..." : "Submit for platform review"}</button>
                    </div>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-100 px-5 py-4">
                      <h3 className="font-semibold text-slate-950">Local candidate review</h3>
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
                          <div className="grid gap-3 p-4 text-sm lg:grid-cols-[140px_minmax(0,1fr)_90px_100px_180px]" key={candidate.id}>
                            <span className="font-semibold text-slate-950">{candidateType(candidate)}</span>
                            <span className="min-w-0">
                              <span className="block truncate text-slate-800">{candidateSummary(candidate)}</span>
                              <span className="block truncate text-xs text-slate-500">{candidate.source_excerpt || "No excerpt"}</span>
                            </span>
                            <span>{formatConfidence(candidate.confidence)}</span>
                            <span>{label(candidate.status)}</span>
                            <span className="flex flex-wrap gap-2">
                              <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => reviewCandidate(candidate, targetTypeForTab(tab), "accept")} disabled={!!working}>Accept</button>
                              <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => reviewCandidate(candidate, targetTypeForTab(tab), "reject")} disabled={!!working}>Reject</button>
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState title="No candidates in this tab" body="Run local extraction or switch to another category." />
                    )}
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-100 px-5 py-4">
                      <h3 className="font-semibold text-slate-950">Detected sections</h3>
                    </div>
                    {detail?.sections?.length ? (
                      <div className="grid gap-3 p-4 md:grid-cols-2">
                        {detail.sections.map((section) => (
                          <div className="rounded-md border border-slate-200 p-3 text-sm" key={section.id}>
                            <span className="font-semibold text-slate-950">{section.section_title}</span>
                            <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-blue-700">{label(section.detected_category)}</p>
                            <p className="mt-2 line-clamp-3 text-slate-600">{section.section_text}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState title="No sections detected" body="Run local extraction to detect sections and candidates." />
                    )}
                  </section>
                </>
              ) : (
                <EmptyState title="No local source selected" body="Create or open a source to review agency-local extraction candidates." />
              )}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
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
      <textarea className="mt-1 min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} required={required} />
    </label>
  )
}

function Metric({ label: metricLabel, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metricLabel}</p>
      <p className="mt-2 text-xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function targetTypeForTab(value) {
  return { rules: "rule", prices: "price", communication_rules: "communication_rule", emd_rules: "emd_rule", exceptions: "exception" }[value] || "rule"
}

function candidateType(candidate) {
  return label(candidate.rule_type || candidate.price_type || candidate.communication_type || candidate.emd_type || candidate.exception_type || "candidate")
}

function candidateSummary(candidate) {
  if (candidate.amount) return `${candidate.currency || ""} ${candidate.amount} ${label(candidate.price_basis)}`
  if (candidate.ssr_code || candidate.osi_keyword) return [candidate.communication_type, candidate.ssr_code || candidate.osi_keyword].filter(Boolean).join(" ")
  if (candidate.rfic || candidate.rfisc) return [candidate.emd_type, candidate.rfic, candidate.rfisc].filter(Boolean).join(" / ")
  if (candidate.normalized_condition_json?.age_min || candidate.normalized_condition_json?.age_max) return `Ages ${candidate.normalized_condition_json.age_min || "?"} to ${candidate.normalized_condition_json.age_max || "?"}`
  return candidate.source_excerpt || candidate.id || "Policy candidate"
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
