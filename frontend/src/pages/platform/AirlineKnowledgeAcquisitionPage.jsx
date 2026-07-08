import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const sourceTypes = ["airline_website", "airline_pdf", "airline_manual", "email_from_airline", "gds_help_page", "tariff_note", "agency_contract", "internal_note", "other"]
const reviewStatuses = ["not_started", "in_review", "needs_clarification", "reviewed", "rejected"]
const approvalStatuses = ["not_requested", "pending", "approved", "rejected"]

const defaultFilters = {
  agency_id: "",
  airline: "",
  service_domain: "",
  service_family: "",
  ssr_code: "",
  rfic: "",
  rfisc: "",
  source_type: "",
  review_status: "",
  approval_status: "",
  effective_date: "",
  official_source_flag: "",
}

export default function AirlineKnowledgeAcquisitionPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/airline-knowledge-acquisition${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      acquisitions: response.items || [],
      summary: response.summary || {},
      futureFeeds: response.future_aoie_feeds || [],
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.airline, filters.service_domain, filters.service_family, filters.ssr_code, filters.rfic, filters.rfisc, filters.source_type, filters.review_status, filters.approval_status, filters.effective_date, filters.official_source_flag])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const metrics = [
    ["Acquisitions", state?.acquisitions?.length || 0],
    ["Official sources", state?.summary?.official_source_count || 0],
    ["Policies", state?.summary?.policy_count || 0],
    ["Capabilities", state?.summary?.capability_count || 0],
    ["Constraints", state?.summary?.operational_constraint_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Knowledge Acquisition</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only Airline Operational Knowledge Graph intake for evidence, policy, pricing, capability, and operational constraints. This workspace does not run AI parsing, automatic extraction, scraping, crawling, airline website automation, provider integrations, live airline APIs, recommendations, feasibility checks, pricing calculations, or background workers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Evidence intake</span>
              <span className="rounded-full bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">Operational knowledge graph</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No parser execution</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Acquisition filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="Service domain" value={filters.service_domain} onChange={(value) => setFilters({ ...filters, service_domain: value })} />
              <Field label="Service family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="SSR code" value={filters.ssr_code} onChange={(value) => setFilters({ ...filters, ssr_code: value })} />
              <Field label="RFIC" value={filters.rfic} onChange={(value) => setFilters({ ...filters, rfic: value })} />
              <Field label="RFISC" value={filters.rfisc} onChange={(value) => setFilters({ ...filters, rfisc: value })} />
              <SelectField label="Source type" value={filters.source_type} onChange={(value) => setFilters({ ...filters, source_type: value })} options={sourceTypes.map((item) => [item, formatType(item)])} placeholder="All source types" />
              <SelectField label="Review status" value={filters.review_status} onChange={(value) => setFilters({ ...filters, review_status: value })} options={reviewStatuses.map((item) => [item, formatType(item)])} placeholder="All review" />
              <SelectField label="Approval status" value={filters.approval_status} onChange={(value) => setFilters({ ...filters, approval_status: value })} options={approvalStatuses.map((item) => [item, formatType(item)])} placeholder="All approval" />
              <Field label="Effective date" type="date" value={filters.effective_date} onChange={(value) => setFilters({ ...filters, effective_date: value })} />
              <SelectField label="Official source" value={filters.official_source_flag} onChange={(value) => setFilters({ ...filters, official_source_flag: value })} options={[["true", "Official"], ["false", "Not official"]]} placeholder="Any" />
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Future AOIE linkage</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {(state?.futureFeeds || []).map((item) => <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700" key={item}>{item}</span>)}
            </div>
          </section>

          {state?.acquisitions?.length ? <AcquisitionList acquisitions={state.acquisitions} showAgency /> : <EmptyState title="No acquisition evidence" body="Manually entered airline source evidence metadata will appear here after records are created." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function AcquisitionList({ acquisitions, showAgency = false }) {
  return (
    <section className="space-y-3">
      {acquisitions.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{item.acquisition_display_name || item.acquisition_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.airline_code || item.airline_name || "Airline unset"} · {formatType(item.source_type)} · {formatType(item.acquisition_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Review: {formatType(item.review_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Approval: {formatType(item.approval_status)}</p>
                <p className="mt-1">Effective: {formatDate(item.source_effective_date)}</p>
              </div>
            </div>
          </summary>
          <KnowledgeGraphSections item={item} showAgency={showAgency} />
        </details>
      ))}
    </section>
  )
}

function KnowledgeGraphSections({ item, showAgency }) {
  return (
    <div className="mt-4 space-y-3 text-xs text-slate-600">
      <KnowledgeSection title="Evidence" defaultOpen>
        <div className="grid gap-4 lg:grid-cols-3">
          <DetailBlock title="Official source" lines={[
            `Reference: ${item.acquisition_reference || "Unset"}`,
            `Title: ${item.source_title || "Unset"}`,
            `URL: ${item.source_url || "Unset"}`,
            `Language: ${item.source_language || "Unset"}`,
            `Publication: ${formatDate(item.source_publication_date)}`,
            `Effective: ${formatDate(item.source_effective_date)}`,
            `Retrieved: ${formatDate(item.source_retrieved_date)}`,
            `Official: ${item.official_source_flag ? "Yes" : "No"}`,
            `Hash: ${item.source_hash || "Unset"}`,
          ]} />
          <TextPanel title="Original text" text={item.evidence?.original_text || item.raw_source_text} />
          <TextPanel title="Source excerpt" text={item.source_excerpt || item.evidence?.notes} />
        </div>
      </KnowledgeSection>
      <KnowledgeSection title="Policy">
        <RecordPanel value={item.policy} />
      </KnowledgeSection>
      <KnowledgeSection title="Pricing">
        <RecordPanel value={item.pricing} />
      </KnowledgeSection>
      <KnowledgeSection title="Capability">
        <RecordPanel value={item.capabilities} emptyText="No capability metadata recorded." />
      </KnowledgeSection>
      <KnowledgeSection title="Operational Constraints">
        <RecordPanel value={item.operational_constraints} emptyText="No operational constraint metadata recorded." />
      </KnowledgeSection>
      <KnowledgeSection title="Animal Transport">
        <RecordPanel value={item.animal_transport} emptyText="No animal transport metadata recorded." />
      </KnowledgeSection>
      <KnowledgeSection title="Extra Seat">
        <RecordPanel value={item.extra_seat} emptyText="No extra seat metadata recorded." />
      </KnowledgeSection>
      <KnowledgeSection title="Cabin">
        <RecordPanel value={item.cabin_capabilities} emptyText="No cabin capability metadata recorded." />
      </KnowledgeSection>
      <KnowledgeSection title="Governance">
        <div className="grid gap-4 lg:grid-cols-3">
          <DetailBlock title="Review" lines={[
            `Review: ${formatType(item.review_status)}`,
            `Reviewer: ${item.reviewer || "Unset"}`,
            `Review notes: ${item.review_notes || "Unset"}`,
            `Approval: ${formatType(item.approval_status)}`,
            `Approved by: ${item.approved_by || "Unset"}`,
            `Approved at: ${formatDateTime(item.approved_at)}`,
            `Rejection: ${item.rejection_reason || "Unset"}`,
          ]} />
          <DetailBlock title="Classification" lines={[
            `Domain: ${item.service_domain || "Unset"}`,
            `Family: ${item.service_family || "Unset"}`,
            `Variant: ${item.service_variant || "Unset"}`,
            `SSR / OSI: ${item.ssr_code || "Unset"} / ${item.osi_relevance || "Unset"}`,
            `RFIC / RFISC: ${item.rfic || "Unset"} / ${item.rfisc || "Unset"}`,
            `Passenger need: ${item.passenger_need_category || "Unset"}`,
          ]} />
          <DetailBlock title="Agency" lines={[
            `Agency: ${showAgency ? item.agency_name || item.agency_id || "Platform governed" : item.agency_id || "Agency scoped"}`,
            `Airline: ${item.airline_code || item.airline_name || "Unset"}`,
            `Created by: ${item.created_by || "Unset"}`,
            `Updated by: ${item.updated_by || "Unset"}`,
          ]} />
        </div>
      </KnowledgeSection>
      <KnowledgeSection title="Versioning">
        <DetailBlock title="Versions" lines={[
          `Version: ${item.acquisition_version || "Unset"}`,
          `Previous: ${item.previous_acquisition_id || "Unset"}`,
          `Supersedes: ${formatList(item.supersedes_acquisition_ids)}`,
          `Change summary: ${item.change_summary || "Unset"}`,
          `Detected change: ${item.detected_change_type || "Unset"}`,
        ]} />
      </KnowledgeSection>
      <KnowledgeSection title="Operational Links">
        <DetailBlock title="Future and workspace references" lines={[
          `Parser runs: ${formatList(item.parser_run_ids)}`,
          `Normalized rules: ${formatList(item.normalized_rule_ids)}`,
          `Knowledge versions: ${formatList(item.knowledge_version_ids)}`,
          `Capability matrix: ${formatList(item.capability_matrix_ids)}`,
          `SSR / OSI: ${formatList(item.ssr_osi_workspace_ids)}`,
          `EMD: ${formatList(item.emd_workspace_ids)}`,
          `Ticket: ${formatList(item.ticket_workspace_ids)}`,
          `Document: ${formatList(item.document_workspace_ids)}`,
          `Future feasibility relevance: ${item.operational_feasibility_relevance || "Unset"}`,
          `Notes: ${item.internal_notes || item.source_notes || "Unset"}`,
        ]} />
      </KnowledgeSection>
    </div>
  )
}

function KnowledgeSection({ title, children, defaultOpen = false }) {
  return (
    <details className="rounded-md border border-slate-200 bg-slate-50 p-3" open={defaultOpen}>
      <summary className="cursor-pointer font-semibold text-slate-800">{title}</summary>
      <div className="mt-3">{children}</div>
    </details>
  )
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function DetailBlock({ title, lines }) {
  return (
    <div>
      <p className="font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <div className="mt-2 space-y-1">
        {lines.map((line) => <p key={line}>{line}</p>)}
      </div>
    </div>
  )
}

function TextPanel({ title, text }) {
  return (
    <div>
      <p className="font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <p className="mt-2 max-h-36 overflow-auto whitespace-pre-wrap rounded-md bg-slate-50 p-3 leading-5">{text || "Unset"}</p>
    </div>
  )
}

function RecordPanel({ value, emptyText = "No metadata recorded." }) {
  const hasValue = hasContent(value)
  return (
    <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-md bg-white p-3 text-xs leading-5 text-slate-600">
      {hasValue ? JSON.stringify(value, null, 2) : emptyText}
    </pre>
  )
}

function hasContent(value) {
  if (!value) return false
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === "object") {
    return Object.values(value).some((entry) => {
      if (Array.isArray(entry)) return entry.length > 0
      if (entry && typeof entry === "object") return hasContent(entry)
      return entry !== null && entry !== "" && entry !== false
    })
  }
  return true
}

function Field({ label, value, onChange, type = "text" }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input type={type} className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function SelectField({ label, value, onChange, options, placeholder }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{placeholder}</option>
        {options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}
      </select>
    </label>
  )
}

function queryString(values) {
  const params = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== "") params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function formatType(value) {
  return String(value || "unset").replaceAll("_", " ")
}

function formatDate(value) {
  return value ? String(value).slice(0, 10) : "Unset"
}

function formatDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "Unset"
}

function formatList(items) {
  return (items || []).length ? items.join(", ") : "None"
}
