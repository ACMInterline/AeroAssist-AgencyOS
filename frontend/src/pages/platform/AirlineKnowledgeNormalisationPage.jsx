import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const statuses = ["draft", "captured", "in_review", "approved", "rejected", "superseded", "archived"]
const types = ["animal_taxonomy", "aircraft_taxonomy", "cabin_taxonomy", "service_taxonomy", "unit_normalisation", "terminology_alias", "ssr_mapping", "rfic_rfisc_mapping", "commercial_term_mapping", "operational_term_mapping"]
const reviewStatuses = ["not_started", "in_review", "needs_clarification", "reviewed", "rejected"]
const approvalStatuses = ["not_requested", "pending", "approved", "rejected"]

const defaultFilters = {
  agency_id: "",
  normalisation_status: "",
  normalisation_type: "",
  canonical_code: "",
  taxonomy_domain: "",
  taxonomy_family: "",
  taxonomy_variant: "",
  airline: "",
  ssr_code: "",
  rfic: "",
  rfisc: "",
  review_status: "",
  approval_status: "",
}

export default function AirlineKnowledgeNormalisationPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/airline-knowledge-normalisation${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      normalisations: response.items || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.normalisation_status, filters.normalisation_type, filters.canonical_code, filters.taxonomy_domain, filters.taxonomy_family, filters.taxonomy_variant, filters.airline, filters.ssr_code, filters.rfic, filters.rfisc, filters.review_status, filters.approval_status])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const metrics = [
    ["Records", state?.normalisations?.length || 0],
    ["Hierarchy", state?.summary?.hierarchy_count || 0],
    ["Aliases", state?.summary?.alias_count || 0],
    ["Applicability", state?.summary?.applicability_count || 0],
    ["Knowledge links", state?.summary?.knowledge_link_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Knowledge Normalisation</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only canonical vocabulary for the Airline Operational Knowledge Graph. It maps messy airline, GDS, commercial, and operational terms into structured taxonomy metadata without live evaluation, AI parsing, recommendations, feasibility scoring, pricing calculation, scraping, workers, or providers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Canonical vocabulary</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Normalisation filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Status" value={filters.normalisation_status} onChange={(value) => setFilters({ ...filters, normalisation_status: value })} options={statuses.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <SelectField label="Type" value={filters.normalisation_type} onChange={(value) => setFilters({ ...filters, normalisation_type: value })} options={types.map((item) => [item, formatType(item)])} placeholder="All types" />
              <Field label="Canonical code" value={filters.canonical_code} onChange={(value) => setFilters({ ...filters, canonical_code: value })} />
              <Field label="Taxonomy domain" value={filters.taxonomy_domain} onChange={(value) => setFilters({ ...filters, taxonomy_domain: value })} />
              <Field label="Taxonomy family" value={filters.taxonomy_family} onChange={(value) => setFilters({ ...filters, taxonomy_family: value })} />
              <Field label="Taxonomy variant" value={filters.taxonomy_variant} onChange={(value) => setFilters({ ...filters, taxonomy_variant: value })} />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="SSR code" value={filters.ssr_code} onChange={(value) => setFilters({ ...filters, ssr_code: value })} />
              <Field label="RFIC" value={filters.rfic} onChange={(value) => setFilters({ ...filters, rfic: value })} />
              <Field label="RFISC" value={filters.rfisc} onChange={(value) => setFilters({ ...filters, rfisc: value })} />
              <SelectField label="Review" value={filters.review_status} onChange={(value) => setFilters({ ...filters, review_status: value })} options={reviewStatuses.map((item) => [item, formatType(item)])} placeholder="All review" />
              <SelectField label="Approval" value={filters.approval_status} onChange={(value) => setFilters({ ...filters, approval_status: value })} options={approvalStatuses.map((item) => [item, formatType(item)])} placeholder="All approval" />
            </div>
          </section>

          {state?.normalisations?.length ? <NormalisationList normalisations={state.normalisations} showAgency /> : <EmptyState title="No knowledge normalisations" body="Canonical airline knowledge vocabulary records will appear here after Platform records them." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function NormalisationList({ normalisations, showAgency = false }) {
  return (
    <section className="space-y-3">
      {normalisations.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{item.normalisation_display_name || item.canonical_code || item.normalisation_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.canonical_code || "Code unset"} - {formatType(item.taxonomy_domain)} - {formatType(item.normalisation_type)}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Status: {formatType(item.normalisation_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Review: {formatType(item.review_status)}</p>
                <p className="mt-1">Approval: {formatType(item.approval_status)}</p>
              </div>
            </div>
          </summary>
          <NormalisationSections item={item} showAgency={showAgency} />
        </details>
      ))}
    </section>
  )
}

function NormalisationSections({ item, showAgency }) {
  return (
    <div className="mt-4 space-y-3 text-xs text-slate-600">
      <Section title="Canonical Record" defaultOpen>
        <DetailBlock title="Canonical metadata" lines={[
          `Reference: ${item.normalisation_reference || "Unset"}`,
          `Code: ${item.canonical_code || "Unset"}`,
          `Name: ${item.canonical_name || "Unset"}`,
          `Description: ${item.canonical_description || "Unset"}`,
          `Type: ${formatType(item.normalisation_type)}`,
          `Agency: ${showAgency ? item.agency_name || item.agency_id || "Platform governed" : item.agency_id || "Agency scoped"}`,
        ]} />
      </Section>
      <Section title="Taxonomy Hierarchy">
        <DetailBlock title="Hierarchy" lines={[
          `Domain: ${item.taxonomy_domain || "Unset"}`,
          `Family: ${item.taxonomy_family || "Unset"}`,
          `Variant: ${item.taxonomy_variant || "Unset"}`,
          `Parent: ${item.parent_canonical_id || "Unset"}`,
          `Path: ${formatList(item.hierarchy_path)}`,
          `Level: ${item.hierarchy_level ?? "Unset"}`,
        ]} />
      </Section>
      <Section title="Aliases / Terms">
        <RecordPanel value={terms(item)} />
      </Section>
      <Section title="Applicability">
        <RecordPanel value={applicability(item)} />
      </Section>
      <Section title="Animal Taxonomy">
        <RecordPanel value={animalTaxonomy(item)} />
      </Section>
      <Section title="Aircraft / Cabin Taxonomy">
        <RecordPanel value={aircraftCabinTaxonomy(item)} />
      </Section>
      <Section title="Service Taxonomy">
        <RecordPanel value={serviceTaxonomy(item)} />
      </Section>
      <Section title="Units">
        <RecordPanel value={units(item)} />
      </Section>
      <Section title="Knowledge Links">
        <RecordPanel value={knowledgeLinks(item)} />
      </Section>
      <Section title="Governance">
        <DetailBlock title="Governance" lines={[
          `Review: ${formatType(item.review_status)}`,
          `Reviewer: ${item.reviewer || "Unset"}`,
          `Review notes: ${item.review_notes || "Unset"}`,
          `Approval: ${formatType(item.approval_status)}`,
          `Approved by: ${item.approved_by || "Unset"}`,
          `Approved at: ${formatDateTime(item.approved_at)}`,
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

function RecordPanel({ value, emptyText = "No metadata recorded." }) {
  const content = hasContent(value) ? JSON.stringify(value, null, 2) : emptyText
  return <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-md bg-white p-3 text-xs leading-5 text-slate-600">{content}</pre>
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

function terms(item) {
  return {
    aliases: item.aliases,
    abbreviations: item.abbreviations,
    airline_specific_terms: item.airline_specific_terms,
    gds_terms: item.gds_terms,
    commercial_terms: item.commercial_terms,
    operational_terms: item.operational_terms,
  }
}

function applicability(item) {
  return {
    airline_codes: item.airline_codes,
    country_codes: item.country_codes,
    airport_codes: item.airport_codes,
    aircraft_types: item.aircraft_types,
    cabin_codes: item.cabin_codes,
    service_codes: item.service_codes,
    ssr_codes: item.ssr_codes,
    rfic_codes: item.rfic_codes,
    rfisc_codes: item.rfisc_codes,
  }
}

function animalTaxonomy(item) {
  return {
    species: item.species,
    breed: item.breed,
    breed_group: item.breed_group,
    brachycephalic_flag: item.brachycephalic_flag,
    restricted_breed_flag: item.restricted_breed_flag,
    service_animal_flag: item.service_animal_flag,
    emotional_support_animal_flag: item.emotional_support_animal_flag,
    animal_notes: item.animal_notes,
  }
}

function aircraftCabinTaxonomy(item) {
  return {
    aircraft_family: item.aircraft_family,
    aircraft_subtype: item.aircraft_subtype,
    cabin_family: item.cabin_family,
    cabin_name: item.cabin_name,
    seat_type: item.seat_type,
    fixed_armrest_flag: item.fixed_armrest_flag,
    adjacent_seat_relevance: item.adjacent_seat_relevance,
    under_seat_space_relevance: item.under_seat_space_relevance,
    cabin_notes: item.cabin_notes,
  }
}

function serviceTaxonomy(item) {
  return {
    passenger_need_category: item.passenger_need_category,
    service_domain: item.service_domain,
    service_family: item.service_family,
    service_variant: item.service_variant,
    related_ssr_code: item.related_ssr_code,
    related_osi_relevance: item.related_osi_relevance,
    related_emd_relevance: item.related_emd_relevance,
    related_document_relevance: item.related_document_relevance,
  }
}

function units(item) {
  return {
    unit_type: item.unit_type,
    canonical_unit: item.canonical_unit,
    unit_aliases: item.unit_aliases,
    conversion_notes: item.conversion_notes,
  }
}

function knowledgeLinks(item) {
  return {
    acquisition_ids: item.acquisition_ids,
    constraint_ids: item.constraint_ids,
    evidence_reference_ids: item.evidence_reference_ids,
    policy_reference_ids: item.policy_reference_ids,
    pricing_reference_ids: item.pricing_reference_ids,
    capability_reference_ids: item.capability_reference_ids,
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
