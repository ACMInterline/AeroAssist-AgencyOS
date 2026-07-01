import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"

const tabs = [
  ["domains", "Domains"],
  ["families", "Families"],
  ["variants", "Variants"],
  ["aliases", "Airline aliases"],
  ["rules", "Mapping rules"],
  ["links", "Candidate links"],
  ["corrections", "Review corrections"],
]

const initialDomain = { code: "", name: "", description: "" }
const initialFamily = { domain_code: "children", code: "", name: "", default_ssr_codes: "" }
const initialVariant = { domain_code: "children", family_code: "unaccompanied_minor", code: "", name: "", standard_ssr_code: "", known_airline_terms: "" }
const initialAlias = { airline_code: "", alias_text: "", alias_type: "policy_term", domain_code: "children", family_code: "unaccompanied_minor", variant_code: "" }
const initialRule = { rule_name: "", airline_code: "", match_type: "exact", match_value: "", domain_code: "children", family_code: "unaccompanied_minor", variant_code: "", priority: "100" }

export default function ServiceTaxonomyPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("domains")
  const [forms, setForms] = useState({
    domain: initialDomain,
    family: initialFamily,
    variant: initialVariant,
    alias: initialAlias,
    rule: initialRule,
  })
  const [mapForm, setMapForm] = useState({ airline_code: "AF", text: "Kids Solo" })
  const [mapResult, setMapResult] = useState(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const [platform, summary, domains, families, variants, aliases, rules, links, corrections, dimensions, outcomes] = await Promise.all([
      apiGet("/api/platform/summary"),
      apiGet("/api/platform/service-taxonomy/summary"),
      apiGet("/api/platform/service-taxonomy/domains"),
      apiGet("/api/platform/service-taxonomy/families"),
      apiGet("/api/platform/service-taxonomy/variants"),
      apiGet("/api/platform/service-taxonomy/aliases"),
      apiGet("/api/platform/service-taxonomy/mapping-rules"),
      apiGet("/api/platform/service-taxonomy/candidate-links"),
      apiGet("/api/platform/service-taxonomy/review-corrections"),
      apiGet("/api/platform/service-taxonomy/applicability-dimensions"),
      apiGet("/api/platform/service-taxonomy/outcome-types"),
    ])
    setState({
      user: platform.current_user,
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

  async function seedBaseline() {
    setWorking("seed")
    setError("")
    setMessage("")
    try {
      const result = await apiPost("/api/platform/service-taxonomy/seed-baseline", {})
      setMessage(`Baseline seed complete. Created ${Object.values(result.created || {}).reduce((sum, value) => sum + Number(value || 0), 0)} records.`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function submitRecord(kind, path, payload, reset) {
    setWorking(kind)
    setError("")
    setMessage("")
    try {
      await apiPost(path, payload)
      setMessage(`${label(kind)} saved.`)
      setForms((current) => ({ ...current, [kind]: reset }))
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function archiveRecord(path) {
    setWorking(path)
    setError("")
    try {
      await apiPatch(path, { status: "archived" })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function testMapping(event) {
    event.preventDefault()
    setWorking("map")
    setError("")
    try {
      setMapResult(await apiPost("/api/platform/service-taxonomy/map-candidate", cleanPayload(mapForm)))
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
    ["Corrections", state?.summary?.review_correction_count],
  ], [state])

  return (
    <PlatformLayout user={state?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Service Taxonomy</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Canonical Service Taxonomy</h2>
              <p className="mt-1 text-sm text-slate-600">Platform owns global taxonomy. Agency corrections require review before global promotion.</p>
            </div>
            <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={seedBaseline} disabled={working === "seed"}>
              {working === "seed" ? "Seeding..." : "Seed baseline"}
            </button>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4 xl:grid-cols-7">
            {summaryCards.map(([cardLabel, value]) => <Metric label={cardLabel} value={value ?? 0} key={cardLabel} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="space-y-4">
              <MappingPanel form={mapForm} setForm={setMapForm} result={mapResult} onSubmit={testMapping} working={working === "map"} />
              <FormPanel title="Create domain" onSubmit={() => submitRecord("domain", "/api/platform/service-taxonomy/domains", forms.domain, initialDomain)}>
                <Field label="Code" value={forms.domain.code} onChange={(value) => setForms({ ...forms, domain: { ...forms.domain, code: value } })} required />
                <Field label="Name" value={forms.domain.name} onChange={(value) => setForms({ ...forms, domain: { ...forms.domain, name: value } })} required />
                <TextArea label="Description" value={forms.domain.description} onChange={(value) => setForms({ ...forms, domain: { ...forms.domain, description: value } })} />
              </FormPanel>
              <FormPanel title="Create family" onSubmit={() => submitRecord("family", "/api/platform/service-taxonomy/families", familyPayload(forms.family), initialFamily)}>
                <Field label="Domain code" value={forms.family.domain_code} onChange={(value) => setForms({ ...forms, family: { ...forms.family, domain_code: value } })} required />
                <Field label="Code" value={forms.family.code} onChange={(value) => setForms({ ...forms, family: { ...forms.family, code: value } })} required />
                <Field label="Name" value={forms.family.name} onChange={(value) => setForms({ ...forms, family: { ...forms.family, name: value } })} required />
                <Field label="Default SSR codes" value={forms.family.default_ssr_codes} onChange={(value) => setForms({ ...forms, family: { ...forms.family, default_ssr_codes: value } })} />
              </FormPanel>
              <FormPanel title="Create variant" onSubmit={() => submitRecord("variant", "/api/platform/service-taxonomy/variants", variantPayload(forms.variant), initialVariant)}>
                <Field label="Domain code" value={forms.variant.domain_code} onChange={(value) => setForms({ ...forms, variant: { ...forms.variant, domain_code: value } })} required />
                <Field label="Family code" value={forms.variant.family_code} onChange={(value) => setForms({ ...forms, variant: { ...forms.variant, family_code: value } })} required />
                <Field label="Code" value={forms.variant.code} onChange={(value) => setForms({ ...forms, variant: { ...forms.variant, code: value } })} required />
                <Field label="Name" value={forms.variant.name} onChange={(value) => setForms({ ...forms, variant: { ...forms.variant, name: value } })} required />
                <Field label="Standard SSR code" value={forms.variant.standard_ssr_code} onChange={(value) => setForms({ ...forms, variant: { ...forms.variant, standard_ssr_code: value.toUpperCase() } })} />
                <Field label="Known airline terms" value={forms.variant.known_airline_terms} onChange={(value) => setForms({ ...forms, variant: { ...forms.variant, known_airline_terms: value } })} />
              </FormPanel>
              <FormPanel title="Create alias" onSubmit={() => submitRecord("alias", "/api/platform/service-taxonomy/aliases", cleanPayload(forms.alias), initialAlias)}>
                <Field label="Airline code" value={forms.alias.airline_code} onChange={(value) => setForms({ ...forms, alias: { ...forms.alias, airline_code: value.toUpperCase() } })} />
                <Field label="Alias text" value={forms.alias.alias_text} onChange={(value) => setForms({ ...forms, alias: { ...forms.alias, alias_text: value } })} required />
                <Select label="Alias type" value={forms.alias.alias_type} options={["policy_term", "commercial_name", "ssr_code", "gds_code", "ndc_label", "internal_label", "other"]} onChange={(value) => setForms({ ...forms, alias: { ...forms.alias, alias_type: value } })} />
                <Field label="Domain code" value={forms.alias.domain_code} onChange={(value) => setForms({ ...forms, alias: { ...forms.alias, domain_code: value } })} required />
                <Field label="Family code" value={forms.alias.family_code} onChange={(value) => setForms({ ...forms, alias: { ...forms.alias, family_code: value } })} required />
                <Field label="Variant code" value={forms.alias.variant_code} onChange={(value) => setForms({ ...forms, alias: { ...forms.alias, variant_code: value } })} />
              </FormPanel>
              <FormPanel title="Create mapping rule" onSubmit={() => submitRecord("rule", "/api/platform/service-taxonomy/mapping-rules", rulePayload(forms.rule), initialRule)}>
                <Field label="Rule name" value={forms.rule.rule_name} onChange={(value) => setForms({ ...forms, rule: { ...forms.rule, rule_name: value } })} required />
                <Field label="Airline code" value={forms.rule.airline_code} onChange={(value) => setForms({ ...forms, rule: { ...forms.rule, airline_code: value.toUpperCase() } })} />
                <Select label="Match type" value={forms.rule.match_type} options={["exact", "contains", "token", "ssr_code", "regex"]} onChange={(value) => setForms({ ...forms, rule: { ...forms.rule, match_type: value } })} />
                <Field label="Match value" value={forms.rule.match_value} onChange={(value) => setForms({ ...forms, rule: { ...forms.rule, match_value: value } })} required />
                <Field label="Domain code" value={forms.rule.domain_code} onChange={(value) => setForms({ ...forms, rule: { ...forms.rule, domain_code: value } })} required />
                <Field label="Family code" value={forms.rule.family_code} onChange={(value) => setForms({ ...forms, rule: { ...forms.rule, family_code: value } })} required />
                <Field label="Variant code" value={forms.rule.variant_code} onChange={(value) => setForms({ ...forms, rule: { ...forms.rule, variant_code: value } })} />
                <Field label="Priority" value={forms.rule.priority} onChange={(value) => setForms({ ...forms, rule: { ...forms.rule, priority: value } })} />
              </FormPanel>
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
              <TaxonomyTable tab={tab} state={state} onArchive={archiveRecord} working={working} />
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-5 xl:col-start-2">
              <h3 className="font-semibold text-slate-950">Applicability and outcome vocabularies</h3>
              <div className="mt-4 grid gap-4 lg:grid-cols-2">
                <CompactList title="Applicability dimensions" items={state?.dimensions || []} />
                <CompactList title="Policy outcome types" items={state?.outcomes || []} />
              </div>
            </section>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function TaxonomyTable({ tab, state, onArchive, working }) {
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
    return <EmptyState title={`No ${label(tab)}`} body="Seed or create records to populate this section." />
  }

  return (
    <div className="divide-y divide-slate-100">
      {items.map((item) => (
        <div className="grid gap-3 p-4 text-sm lg:grid-cols-[180px_minmax(0,1fr)_160px_120px]" key={item.id}>
          <div>
            <p className="font-semibold text-slate-950">{item.name || item.rule_name || item.alias_text || item.candidate_id || item.id}</p>
            <p className="text-xs text-slate-500">{item.code || item.match_type || item.candidate_type || item.promotion_status || label(item.status)}</p>
          </div>
          <div className="min-w-0 text-slate-600">
            <p className="truncate">{taxonomyPath(item)}</p>
            <p className="truncate text-xs">{item.description || item.match_value || item.evidence_text || item.correction_reason || item.normalized_alias_text || "No additional note"}</p>
          </div>
          <span className="text-slate-600">{item.airline_code || item.review_status || item.governance_status || item.scope || "global"}</span>
          {["domains", "families", "variants", "aliases", "rules"].includes(tab) ? (
            <button className="rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold disabled:opacity-60" type="button" onClick={() => onArchive(archivePath(tab, item.id))} disabled={working === archivePath(tab, item.id)}>
              Archive
            </button>
          ) : (
            <span className="text-xs text-slate-500">{formatConfidence(item.confidence_score)}</span>
          )}
        </div>
      ))}
    </div>
  )
}

function MappingPanel({ form, setForm, result, onSubmit, working }) {
  return (
    <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={onSubmit}>
      <h3 className="font-semibold text-slate-950">Mapping test</h3>
      <Field label="Airline code" value={form.airline_code} onChange={(value) => setForm({ ...form, airline_code: value.toUpperCase() })} />
      <Field label="Text or code" value={form.text} onChange={(value) => setForm({ ...form, text: value })} required />
      <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working}>{working ? "Mapping..." : "Map candidate"}</button>
      {result ? (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-950">
          <p className="font-semibold">{taxonomyPath(result)} · {formatConfidence(result.confidence_score)}</p>
          <p className="mt-1 text-blue-800">{result.explanation}</p>
        </div>
      ) : null}
    </form>
  )
}

function FormPanel({ title, children, onSubmit }) {
  return (
    <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={(event) => { event.preventDefault(); onSubmit() }}>
      <h3 className="font-semibold text-slate-950">{title}</h3>
      {children}
      <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="submit">Save</button>
    </form>
  )
}

function CompactList({ title, items }) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      <div className="mt-2 max-h-80 divide-y divide-slate-100 overflow-auto rounded-md border border-slate-200">
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

function familyPayload(form) {
  return { ...cleanPayload(form), default_ssr_codes: splitList(form.default_ssr_codes), related_service_catalogue_keys: splitList(form.default_ssr_codes) }
}

function variantPayload(form) {
  return { ...cleanPayload(form), known_airline_terms: splitList(form.known_airline_terms) }
}

function rulePayload(form) {
  return { ...cleanPayload(form), priority: Number(form.priority || 100), confidence_score: 0.84 }
}

function cleanPayload(payload) {
  const clean = { ...payload }
  Object.keys(clean).forEach((key) => {
    if (clean[key] === "") clean[key] = null
  })
  return clean
}

function splitList(value) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean)
}

function archivePath(tab, id) {
  const resource = { domains: "domains", families: "families", variants: "variants", aliases: "aliases", rules: "mapping-rules" }[tab]
  return `/api/platform/service-taxonomy/${resource}/${id}`
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
