import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const tabs = [
  ["domains", "Domains"],
  ["families", "Families"],
  ["variants", "Variants"],
  ["aliases", "Aliases"],
  ["rules", "Mapping rules"],
  ["links", "Candidate links"],
  ["corrections", "Corrections"],
]

export default function ServiceTaxonomyPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("domains")
  const [mapForm, setMapForm] = useState({ airline_code: "AF", text: "Kids Solo" })
  const [linkForm, setLinkForm] = useState({ candidate_type: "extracted_rule", candidate_id: "", evidence_text: "Kids Solo assistance requested", airline_code: "AF" })
  const [correctionForm, setCorrectionForm] = useState({ corrected_domain_code: "children", corrected_family_code: "unaccompanied_minor", corrected_variant_code: "kids_solo", correction_reason: "", promotion_requested: false })
  const [mapResult, setMapResult] = useState(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/service-taxonomy`
    const [summary, domains, families, variants, aliases, rules, links, corrections, dimensions, outcomes] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/domains`),
      apiGet(`${base}/families`),
      apiGet(`${base}/variants`),
      apiGet(`${base}/aliases`),
      apiGet(`${base}/mapping-rules`),
      apiGet(`${base}/candidate-links`),
      apiGet(`${base}/review-corrections`),
      apiGet(`${base}/applicability-dimensions`),
      apiGet(`${base}/outcome-types`),
    ])
    setState({
      ...context,
      base,
      summary,
      domains: domains.items || [],
      families: families.items || [],
      variants: variants.items || [],
      aliases: aliases.items || [],
      rules: rules.items || [],
      links: links.items || [],
      corrections: corrections.items || [],
      dimensions: dimensions.items || [],
      outcomes: outcomes.items || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function mapCandidate(event) {
    event.preventDefault()
    setWorking("map")
    setError("")
    try {
      setMapResult(await apiPost(`${state.base}/map-candidate`, cleanPayload(mapForm)))
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function createLink(event) {
    event.preventDefault()
    setWorking("link")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/candidate-links`, cleanPayload(linkForm))
      setMessage(`Agency-local taxonomy link saved as ${label(result.link.review_status)}.`)
      setLinkForm({ ...linkForm, candidate_id: "" })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function createCorrection(event) {
    event.preventDefault()
    const link = state.links[0]
    const candidateId = link?.candidate_id || linkForm.candidate_id
    if (!candidateId) {
      setError("Create a candidate link or enter a candidate id before saving a correction.")
      return
    }
    setWorking("correction")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/review-corrections`, {
        policy_candidate_taxonomy_link_id: link?.id || null,
        candidate_type: link?.candidate_type || linkForm.candidate_type,
        candidate_id: candidateId,
        previous_domain_code: link?.domain_code || null,
        previous_family_code: link?.family_code || null,
        previous_variant_code: link?.variant_code || null,
        corrected_domain_code: correctionForm.corrected_domain_code,
        corrected_family_code: correctionForm.corrected_family_code,
        corrected_variant_code: correctionForm.corrected_variant_code || null,
        correction_reason: correctionForm.correction_reason,
        promotion_requested: correctionForm.promotion_requested,
      })
      setMessage(`Correction saved. Promotion status: ${label(result.promotion_status)}.`)
      setCorrectionForm({ ...correctionForm, correction_reason: "", promotion_requested: false })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function markLinkConfirmed(link) {
    setWorking(link.id)
    setError("")
    try {
      await apiPatch(`${state.base}/candidate-links/${link.id}`, { review_status: "confirmed" })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  const summaryCards = useMemo(() => [
    ["Domains", state?.summary?.domain_count],
    ["Families", state?.summary?.family_count],
    ["Variants", state?.summary?.variant_count],
    ["Aliases", state?.summary?.alias_count],
    ["Rules", state?.summary?.mapping_rule_count],
    ["Links", state?.summary?.candidate_link_count],
  ], [state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Service Taxonomy</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Canonical Service Taxonomy</h2>
              <p className="mt-1 text-sm text-slate-600">Global taxonomy is read-only here. Agency corrections stay local until platform review.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No global mutation controls</span>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {summaryCards.map(([cardLabel, value]) => <Metric label={cardLabel} value={value ?? 0} key={cardLabel} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={mapCandidate}>
                <h3 className="font-semibold text-slate-950">Mapping test</h3>
                <Field label="Airline code" value={mapForm.airline_code} onChange={(value) => setMapForm({ ...mapForm, airline_code: value.toUpperCase() })} />
                <Field label="Text or code" value={mapForm.text} onChange={(value) => setMapForm({ ...mapForm, text: value })} required />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "map"}>{working === "map" ? "Mapping..." : "Map candidate"}</button>
                {mapResult ? (
                  <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-950">
                    <p className="font-semibold">{taxonomyPath(mapResult)} · {formatConfidence(mapResult.confidence_score)}</p>
                    <p className="mt-1 text-blue-800">{mapResult.explanation}</p>
                  </div>
                ) : null}
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createLink}>
                <h3 className="font-semibold text-slate-950">Create local candidate link</h3>
                <Select label="Candidate type" value={linkForm.candidate_type} options={["extracted_rule", "extracted_price", "extracted_communication", "extracted_emd_rule", "extracted_exception", "approved_knowledge"]} onChange={(value) => setLinkForm({ ...linkForm, candidate_type: value })} />
                <Field label="Candidate id" value={linkForm.candidate_id} onChange={(value) => setLinkForm({ ...linkForm, candidate_id: value })} required />
                <Field label="Airline code" value={linkForm.airline_code} onChange={(value) => setLinkForm({ ...linkForm, airline_code: value.toUpperCase() })} />
                <TextArea label="Evidence text" value={linkForm.evidence_text} onChange={(value) => setLinkForm({ ...linkForm, evidence_text: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "link"}>{working === "link" ? "Saving..." : "Save local link"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createCorrection}>
                <h3 className="font-semibold text-slate-950">Local correction note</h3>
                <Field label="Corrected domain" value={correctionForm.corrected_domain_code} onChange={(value) => setCorrectionForm({ ...correctionForm, corrected_domain_code: value })} required />
                <Field label="Corrected family" value={correctionForm.corrected_family_code} onChange={(value) => setCorrectionForm({ ...correctionForm, corrected_family_code: value })} required />
                <Field label="Corrected variant" value={correctionForm.corrected_variant_code} onChange={(value) => setCorrectionForm({ ...correctionForm, corrected_variant_code: value })} />
                <TextArea label="Review note" value={correctionForm.correction_reason} onChange={(value) => setCorrectionForm({ ...correctionForm, correction_reason: value })} />
                <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                  <input type="checkbox" checked={correctionForm.promotion_requested} onChange={(event) => setCorrectionForm({ ...correctionForm, promotion_requested: event.target.checked })} />
                  Request platform review
                </label>
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "correction"}>{working === "correction" ? "Saving..." : "Save correction"}</button>
              </form>
            </div>

            <section className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-100 px-5 py-4">
                <div className="flex flex-wrap gap-2">
                  {tabs.map(([key, title]) => (
                    <button className={`rounded-md px-3 py-2 text-sm font-semibold ${tab === key ? "bg-blue-600 text-white" : "border border-slate-300 text-slate-700"}`} type="button" key={key} onClick={() => setTab(key)}>
                      {title}
                    </button>
                  ))}
                </div>
              </div>
              <TaxonomyTable tab={tab} state={state} onConfirm={markLinkConfirmed} working={working} />
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-5 xl:col-start-2">
              <h3 className="font-semibold text-slate-950">Applicability and outcomes</h3>
              <div className="mt-4 grid gap-4 lg:grid-cols-2">
                <CompactList title="Applicability dimensions" items={state?.dimensions || []} />
                <CompactList title="Outcome types" items={state?.outcomes || []} />
              </div>
            </section>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function TaxonomyTable({ tab, state, onConfirm, working }) {
  const items = {
    domains: state?.domains,
    families: state?.families,
    variants: state?.variants,
    aliases: state?.aliases,
    rules: state?.rules,
    links: state?.links,
    corrections: state?.corrections,
  }[tab] || []

  if (!items.length) {
    return <EmptyState title={`No ${label(tab)}`} body="Records will appear here when available." />
  }

  return (
    <div className="divide-y divide-slate-100">
      {items.map((item) => (
        <div className="grid gap-3 p-4 text-sm lg:grid-cols-[180px_minmax(0,1fr)_160px_130px]" key={item.id}>
          <div>
            <p className="font-semibold text-slate-950">{item.name || item.rule_name || item.alias_text || item.candidate_id || item.id}</p>
            <p className="text-xs text-slate-500">{item.code || item.match_type || item.candidate_type || label(item.status)}</p>
          </div>
          <div className="min-w-0 text-slate-600">
            <p className="truncate">{taxonomyPath(item)}</p>
            <p className="truncate text-xs">{item.description || item.match_value || item.evidence_text || item.correction_reason || item.normalized_alias_text || "No additional note"}</p>
          </div>
          <span className="text-slate-600">{item.airline_code || item.review_status || item.governance_status || item.promotion_status || "global"}</span>
          {tab === "links" ? (
            <button className="rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold disabled:opacity-60" type="button" onClick={() => onConfirm(item)} disabled={working === item.id}>
              Confirm
            </button>
          ) : (
            <span className="text-xs text-slate-500">{formatConfidence(item.confidence_score)}</span>
          )}
        </div>
      ))}
    </div>
  )
}

function CompactList({ title, items }) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      <div className="mt-2 max-h-72 divide-y divide-slate-100 overflow-auto rounded-md border border-slate-200">
        {items.map((item) => (
          <div className="p-3 text-sm" key={item.id}>
            <p className="font-semibold text-slate-950">{item.name}</p>
            <p className="text-xs text-slate-500">{item.code} · {item.value_type || item.severity}</p>
          </div>
        ))}
      </div>
    </div>
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

function Field({ label: fieldLabel, value, onChange, required = false }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} required={required} />
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
        {options.map((option) => <option value={option} key={option}>{label(option)}</option>)}
      </select>
    </label>
  )
}

function cleanPayload(payload) {
  const clean = { ...payload }
  Object.keys(clean).forEach((key) => {
    if (clean[key] === "") clean[key] = null
  })
  return clean
}

function taxonomyPath(item) {
  return [item.domain_code, item.family_code, item.variant_code].filter(Boolean).join(" / ") || item.code || "not mapped"
}

function formatConfidence(value) {
  const number = Number(value)
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "not set"
}

function label(value) {
  return String(value || "not set").replaceAll("_", " ")
}
