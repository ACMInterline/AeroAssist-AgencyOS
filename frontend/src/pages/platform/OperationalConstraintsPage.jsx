import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const statuses = ["draft", "captured", "in_review", "approved", "rejected", "superseded", "archived"]
const outcomes = ["allowed", "not_allowed", "approval_required", "document_required", "emd_required", "manual_review_required", "embargo", "restriction_applies", "pricing_rule_applies", "refund_condition_applies", "capability_available", "capability_unavailable"]
const reviewStatuses = ["not_started", "in_review", "needs_clarification", "reviewed", "rejected"]
const approvalStatuses = ["not_requested", "pending", "approved", "rejected"]

const defaultFilters = {
  agency_id: "",
  acquisition_id: "",
  airline: "",
  service_domain: "",
  service_family: "",
  ssr_code: "",
  rfic: "",
  rfisc: "",
  constraint_status: "",
  outcome_type: "",
  review_status: "",
  approval_status: "",
  evaluation_ready: "",
}

export default function OperationalConstraintsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/operational-constraints${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      constraints: response.items || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.acquisition_id, filters.airline, filters.service_domain, filters.service_family, filters.ssr_code, filters.rfic, filters.rfisc, filters.constraint_status, filters.outcome_type, filters.review_status, filters.approval_status, filters.evaluation_ready])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const metrics = [
    ["Constraints", state?.constraints?.length || 0],
    ["Conditions", state?.summary?.condition_count || 0],
    ["Groups", state?.summary?.condition_group_count || 0],
    ["Evidence links", state?.summary?.evidence_link_count || 0],
    ["Operational links", state?.summary?.operational_link_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Operational Constraints</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only AOIE constraint language for future reasoning. This page stores and displays condition groups, outcomes, applicability, precedence, governance, and future evaluation notes without live rule execution, AI reasoning, recommendations, feasibility scoring, pricing calculation, parser execution, scraping, workers, or providers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Constraint language</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No live evaluation</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Constraint filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <Field label="Acquisition" value={filters.acquisition_id} onChange={(value) => setFilters({ ...filters, acquisition_id: value })} />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="Service domain" value={filters.service_domain} onChange={(value) => setFilters({ ...filters, service_domain: value })} />
              <Field label="Service family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="SSR code" value={filters.ssr_code} onChange={(value) => setFilters({ ...filters, ssr_code: value })} />
              <Field label="RFIC" value={filters.rfic} onChange={(value) => setFilters({ ...filters, rfic: value })} />
              <Field label="RFISC" value={filters.rfisc} onChange={(value) => setFilters({ ...filters, rfisc: value })} />
              <SelectField label="Status" value={filters.constraint_status} onChange={(value) => setFilters({ ...filters, constraint_status: value })} options={statuses.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <SelectField label="Outcome" value={filters.outcome_type} onChange={(value) => setFilters({ ...filters, outcome_type: value })} options={outcomes.map((item) => [item, formatType(item)])} placeholder="All outcomes" />
              <SelectField label="Review" value={filters.review_status} onChange={(value) => setFilters({ ...filters, review_status: value })} options={reviewStatuses.map((item) => [item, formatType(item)])} placeholder="All review" />
              <SelectField label="Approval" value={filters.approval_status} onChange={(value) => setFilters({ ...filters, approval_status: value })} options={approvalStatuses.map((item) => [item, formatType(item)])} placeholder="All approval" />
              <SelectField label="Evaluation ready" value={filters.evaluation_ready} onChange={(value) => setFilters({ ...filters, evaluation_ready: value })} options={[["true", "Ready metadata"], ["false", "Not ready"]]} placeholder="Any" />
            </div>
          </section>

          {state?.constraints?.length ? <ConstraintList constraints={state.constraints} showAgency /> : <EmptyState title="No operational constraints" body="Metadata-only operational constraints will appear here after Platform records them." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function ConstraintList({ constraints, showAgency = false }) {
  return (
    <section className="space-y-3">
      {constraints.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{item.constraint_display_name || item.constraint_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.airline_code || "Airline unset"} · {formatType(item.service_domain)} · {formatType(item.outcome_type)}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Status: {formatType(item.constraint_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Review: {formatType(item.review_status)}</p>
                <p className="mt-1">Approval: {formatType(item.approval_status)}</p>
              </div>
            </div>
          </summary>
          <ConstraintSections item={item} showAgency={showAgency} />
        </details>
      ))}
    </section>
  )
}

function ConstraintSections({ item, showAgency }) {
  return (
    <div className="mt-4 space-y-3 text-xs text-slate-600">
      <Section title="Constraint Overview" defaultOpen>
        <DetailBlock title="Overview" lines={[
          `Reference: ${item.constraint_reference || "Unset"}`,
          `Name: ${item.constraint_name || "Unset"}`,
          `Description: ${item.constraint_description || "Unset"}`,
          `Version: ${item.constraint_version || "Unset"}`,
          `Created by: ${item.created_by || "Unset"}`,
          `Agency: ${showAgency ? item.agency_name || item.agency_id || "Platform governed" : item.agency_id || "Agency scoped"}`,
        ]} />
      </Section>
      <Section title="Knowledge Link">
        <DetailBlock title="Knowledge reference" lines={[
          `Acquisition: ${item.acquisition_id || "Unset"}`,
          `Airline: ${item.airline_code || "Unset"}`,
          `Domain: ${item.service_domain || "Unset"}`,
          `Family: ${item.service_family || "Unset"}`,
          `Variant: ${item.service_variant || "Unset"}`,
          `SSR: ${item.ssr_code || "Unset"}`,
          `RFIC / RFISC: ${item.rfic || "Unset"} / ${item.rfisc || "Unset"}`,
        ]} />
      </Section>
      <Section title="Conditions">
        <div className="grid gap-4 lg:grid-cols-2">
          <RecordPanel title="Condition groups" value={item.condition_groups} emptyText="No condition groups recorded." />
          <RecordPanel title="Ungrouped conditions" value={item.conditions} emptyText="No direct conditions recorded." />
        </div>
      </Section>
      <Section title="Outcomes">
        <DetailBlock title="Outcome" lines={[
          `Type: ${formatType(item.outcome_type)}`,
          `Value: ${formatValue(item.outcome_value)}`,
          `Severity: ${item.outcome_severity || "Unset"}`,
          `Reason: ${item.outcome_reason || "Unset"}`,
          `Notes: ${item.outcome_notes || "Unset"}`,
        ]} />
      </Section>
      <Section title="Applicability">
        <RecordPanel value={applicability(item)} />
      </Section>
      <Section title="Priority / Precedence">
        <DetailBlock title="Priority" lines={[
          `Priority: ${item.constraint_priority || "Unset"}`,
          `Conflict resolution: ${item.conflict_resolution_hint || "Unset"}`,
          `Precedence group: ${item.precedence_group || "Unset"}`,
        ]} />
      </Section>
      <Section title="Governance">
        <DetailBlock title="Governance" lines={[
          `Evidence: ${formatList(item.evidence_reference_ids)}`,
          `Review: ${formatType(item.review_status)}`,
          `Reviewer: ${item.reviewer || "Unset"}`,
          `Review notes: ${item.review_notes || "Unset"}`,
          `Approval: ${formatType(item.approval_status)}`,
          `Approved by: ${item.approved_by || "Unset"}`,
          `Approved at: ${formatDateTime(item.approved_at)}`,
        ]} />
      </Section>
      <Section title="Future Evaluation">
        <DetailBlock title="Evaluation metadata" lines={[
          `Ready metadata: ${item.evaluation_ready ? "Yes" : "No"}`,
          `Notes: ${item.evaluation_notes || "Unset"}`,
          `Compatibility: ${item.future_engine_compatibility || "Unset"}`,
          "Live evaluation: Disabled",
        ]} />
      </Section>
      <Section title="Operational Links">
        <DetailBlock title="Workspace references" lines={[
          `SSR / OSI: ${formatList(item.ssr_osi_workspace_ids)}`,
          `EMD: ${formatList(item.emd_workspace_ids)}`,
          `Documents: ${formatList(item.document_workspace_ids)}`,
          `Workflows: ${formatList(item.workflow_ids)}`,
          `Timelines: ${formatList(item.timeline_ids)}`,
          `Internal notes: ${item.internal_notes || "Unset"}`,
        ]} />
      </Section>
    </div>
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

function Section({ title, children, defaultOpen = false }) {
  return (
    <details className="rounded-md border border-slate-200 bg-slate-50 p-3" open={defaultOpen}>
      <summary className="cursor-pointer font-semibold text-slate-800">{title}</summary>
      <div className="mt-3">{children}</div>
    </details>
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

function RecordPanel({ title, value, emptyText = "No metadata recorded." }) {
  const content = hasContent(value) ? JSON.stringify(value, null, 2) : emptyText
  return (
    <div>
      {title ? <p className="font-semibold uppercase tracking-wide text-slate-500">{title}</p> : null}
      <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap rounded-md bg-white p-3 text-xs leading-5 text-slate-600">{content}</pre>
    </div>
  )
}

function Field({ label, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input type="text" className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
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

function applicability(item) {
  return {
    airline_applicability: item.airline_applicability,
    route_applicability: item.route_applicability,
    origin_country_applicability: item.origin_country_applicability,
    destination_country_applicability: item.destination_country_applicability,
    airport_applicability: item.airport_applicability,
    aircraft_applicability: item.aircraft_applicability,
    cabin_applicability: item.cabin_applicability,
    passenger_type_applicability: item.passenger_type_applicability,
    species_applicability: item.species_applicability,
    breed_applicability: item.breed_applicability,
    seasonal_applicability: item.seasonal_applicability,
    date_range_applicability: item.date_range_applicability,
  }
}

function queryString(values) {
  const params = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== "") params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function hasContent(value) {
  if (!value) return false
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === "object") return Object.values(value).some((entry) => hasContent(entry))
  return value !== ""
}

function formatType(value) {
  return String(value || "unset").replaceAll("_", " ")
}

function formatDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "Unset"
}

function formatList(items) {
  return (items || []).length ? items.join(", ") : "None"
}

function formatValue(value) {
  if (value === undefined || value === null || value === "") return "Unset"
  if (typeof value === "object") return JSON.stringify(value)
  return String(value)
}
